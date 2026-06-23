# ============================================================
# Alap Bot — app.py  Phase 1 + Phase 2
# Handles: Checkout, Cart, Orders, Courier, bKash, Broadcasts,
#          Comment-to-DM, Profit, Abandoned-cart recovery
# ============================================================

import json, os, re, uuid, base64, time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Allow Client Panel (browser) to call these endpoints

CUSTOMERS_FILE = "customers.json"

# ─── helpers ────────────────────────────────────────────────
def load_data():
    try:
        with open(CUSTOMERS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"pages": []}

def save_data(data):
    with open(CUSTOMERS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_clients():
    data = load_data()
    return {c["page_id"]: c for c in data.get("pages", [])}

def get_client_by_token(token):
    """Find client by their panel_token (used by Client Panel API calls)."""
    data = load_data()
    for c in data.get("pages", []):
        if c.get("panel_token") == token:
            return c
    return None

def update_client(page_id, updated):
    """Persist a single client's record back to customers.json."""
    data = load_data()
    for i, c in enumerate(data["pages"]):
        if c["page_id"] == page_id:
            data["pages"][i] = updated
            save_data(data)
            return
    # Not found — append
    data["pages"].append(updated)
    save_data(data)

def order_id():
    return "ORD-" + uuid.uuid4().hex[:8].upper()

def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

# ─── Delivery fee logic ──────────────────────────────────────
DHAKA_KEYWORDS = ["dhaka", "ঢাকা", "mirpur", "uttara", "gulshan", "dhanmondi",
                  "banani", "motijheel", "tejgaon", "mohammadpur", "rampura",
                  "badda", "khilgaon", "malibagh", "bashundhara"]

def calc_delivery_fee(address):
    addr_lower = address.lower()
    if any(kw in addr_lower for kw in DHAKA_KEYWORDS):
        return 60, "Inside Dhaka"
    return 120, "Outside Dhaka"

# ─── Product search ──────────────────────────────────────────
def find_products(query, inventory):
    q = query.lower()
    return [p for p in inventory if q in p.get("name","").lower() or q in p.get("details","").lower()]

def inventory_text(inventory):
    lines = []
    for p in inventory:
        if p.get("stock", 0) > 0:
            lines.append(f"- {p['name']} (৳{p['price']}) — {p.get('details','')}")
    return "\n".join(lines) if lines else "No products currently in stock."

# ─── Q&A context ────────────────────────────────────────────
def qa_context(qa_list):
    if not qa_list:
        return ""
    ctx = "\n\nCommon Q&A:\n"
    for item in qa_list:
        ctx += f"Q: {item['q']}\nA: {item['a']}\n"
    return ctx

# ─── Groq AI reply ──────────────────────────────────────────
def ai_reply(message, client_config, extra_context=""):
    inventory = client_config.get("inventory", [])
    qa = client_config.get("qa", [])
    style = client_config.get("greeting_style", "online store")

    system = f"""You are a friendly shop assistant for {style}.
Help customers with their questions about products.
Rules:
- Never reveal exact stock amounts — say "Yes we have it" or "Sorry out of stock"
- Reply in same language as customer (Bangla/English/Banglish all fine)
- Keep replies short — 1-3 sentences max
- Be warm and conversational{qa_context(qa)}{extra_context}"""

    user_msg = f"""Customer: {message}

{inventory_text(inventory)}

Reply to the customer."""

    groq_key = os.environ.get("GROQ_API_KEY") or client_config.get("apiKeys", {}).get("groqKey", "")

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
            json={
                "model": "mixtral-8x7b-32768",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_msg}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            },
            timeout=10
        )
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Groq error: {e}")
        return "আমি এই মুহূর্তে উত্তর দিতে পারছি না। একটু পরে আবার চেষ্টা করুন।"

# ─── Send Facebook message ───────────────────────────────────
def fb_send(recipient_id, text, access_token, buttons=None):
    url = "https://graph.facebook.com/v18.0/me/messages"
    if buttons:
        payload = {
            "recipient": {"id": recipient_id},
            "message": {
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "button",
                        "text": text[:640],
                        "buttons": buttons[:3]
                    }
                }
            }
        }
    else:
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": text[:2000]}
        }
    try:
        r = requests.post(url, json=payload, params={"access_token": access_token}, timeout=8)
        print(f"FB send: {r.status_code}")
    except Exception as e:
        print(f"FB send error: {e}")

# ─── Cart / Checkout state ───────────────────────────────────
# In-memory per sender (Railway restarts clear this — acceptable for MVP)
# Structure: carts[page_id][sender_id] = { items, state, name, phone, address, hold_until }
carts = {}

STATES = {
    "BROWSING": "browsing",
    "ADDING":   "adding",
    "CHECKOUT": "checkout_name",
    "PHONE":    "checkout_phone",
    "ADDRESS":  "checkout_address",
    "CONFIRM":  "checkout_confirm",
    "HOLD":     "held",
    "DONE":     "done",
}

def get_cart(page_id, sender_id):
    carts.setdefault(page_id, {})
    if sender_id not in carts[page_id]:
        carts[page_id][sender_id] = {"items": [], "state": STATES["BROWSING"],
                                      "name": "", "phone": "", "address": "",
                                      "hold_until": None, "last_active": time.time()}
    return carts[page_id][sender_id]

def cart_total(cart, fee):
    subtotal = sum(int(i["price"]) * i["qty"] for i in cart["items"])
    return subtotal, subtotal + fee

def cart_summary(cart):
    lines = []
    for i in cart["items"]:
        lines.append(f"• {i['name']} × {i['qty']} — ৳{int(i['price'])*i['qty']}")
    return "\n".join(lines) if lines else "(empty)"

def is_blacklisted(phone, client_config):
    bl = client_config.get("blacklist", [])
    return any(b.get("phone","") == phone for b in bl)

# ─── Intent detection ────────────────────────────────────────
ORDER_TRIGGERS   = ["order", "buy", "নিতে চাই", "কিনতে চাই", "নেব", "দিন",
                    "কিনব", "অর্ডার", "book", "purchase"]
CANCEL_TRIGGERS  = ["cancel", "বাদ", "না", "stop", "বন্ধ"]
HOLD_TRIGGERS    = ["hold", "রেখে দিন", "hold করুন", "রাখুন"]
DONE_TRIGGERS    = ["done", "ok", "okay", "হয়েছে", "checkout", "proceed", "yes", "হ্যাঁ", "yep"]
CONFIRM_TRIGGERS = ["confirm", "কনফার্ম", "yes", "হ্যাঁ", "ok", "okay", "sure"]
HUMAN_TRIGGERS   = ["human", "agent", "manager", "support", "কথা বলতে চাই", "মানুষের সাথে"]

def has_trigger(msg, triggers):
    m = msg.lower()
    return any(t in m for t in triggers)

# ─── Main message handler ────────────────────────────────────
def handle_message(sender_id, message, client_config, page_id):
    cart = get_cart(page_id, sender_id)
    cart["last_active"] = time.time()
    access_token = client_config["access_token"]
    inventory = client_config.get("inventory", [])
    msg = message.strip()

    # ── Human handoff ──
    if has_trigger(msg, HUMAN_TRIGGERS):
        client_config.setdefault("urgent_chats", [])
        if sender_id not in client_config["urgent_chats"]:
            client_config["urgent_chats"].append(sender_id)
        update_client(page_id, client_config)
        fb_send(sender_id,
            "আমি এখনই আমাদের একজন কর্মীকে জানাচ্ছি। একটু অপেক্ষা করুন — কেউ আপনার সাথে যোগাযোগ করবে। 🙏",
            access_token)
        return

    # ── Hold expiry check ──
    if cart["hold_until"] and time.time() > cart["hold_until"]:
        cart.update({"items": [], "state": STATES["BROWSING"], "hold_until": None})
        fb_send(sender_id, "⏰ আপনার হোল্ড মেয়াদ শেষ হয়ে গেছে। পণ্যগুলো আবার উপলব্ধ হয়ে গেছে।", access_token)

    # ── Cancel ──
    if has_trigger(msg, CANCEL_TRIGGERS) and cart["state"] not in [STATES["BROWSING"]]:
        cart.update({"items": [], "state": STATES["BROWSING"], "hold_until": None})
        fb_send(sender_id, "অর্ডার বাতিল করা হয়েছে। আবার কিছু লাগলে জানাবেন। 😊", access_token)
        return

    # ── Checkout state machine ──
    state = cart["state"]

    if state == STATES["CHECKOUT"]:
        cart["name"] = msg
        cart["state"] = STATES["PHONE"]
        fb_send(sender_id, f"ধন্যবাদ {msg}! আপনার ফোন নম্বরটি দিন:", access_token)
        return

    if state == STATES["PHONE"]:
        phone = re.sub(r"[^\d+]", "", msg)
        if is_blacklisted(phone, client_config):
            fb_send(sender_id, "দুঃখিত, এই নম্বর থেকে অর্ডার নেওয়া সম্ভব নয়।", access_token)
            cart.update({"items": [], "state": STATES["BROWSING"]})
            return
        cart["phone"] = phone
        cart["state"] = STATES["ADDRESS"]
        fb_send(sender_id, "আপনার ডেলিভারি ঠিকানা দিন:", access_token)
        return

    if state == STATES["ADDRESS"]:
        cart["address"] = msg
        fee, zone = calc_delivery_fee(msg)
        subtotal, total = cart_total(cart, fee)
        summary = (
            f"📋 অর্ডার সামারি\n"
            f"{'─'*25}\n"
            f"{cart_summary(cart)}\n"
            f"{'─'*25}\n"
            f"পণ্যের মোট: ৳{subtotal}\n"
            f"ডেলিভারি ({zone}): ৳{fee}\n"
            f"{'─'*25}\n"
            f"মোট: ৳{total}\n\n"
            f"নাম: {cart['name']}\n"
            f"ফোন: {cart['phone']}\n"
            f"ঠিকানা: {msg}\n\n"
            f"কনফার্ম করতে 'confirm' লিখুন অথবা 'cancel' লিখুন।"
        )
        cart["state"] = STATES["CONFIRM"]
        cart["fee"] = fee
        cart["zone"] = zone
        cart["total"] = total
        fb_send(sender_id, summary, access_token)
        return

    if state == STATES["CONFIRM"]:
        if has_trigger(msg, CONFIRM_TRIGGERS):
            # Deduct stock
            for item in cart["items"]:
                for p in inventory:
                    if p["name"] == item["name"]:
                        p["stock"] = max(0, p.get("stock", 0) - item["qty"])
            # Save order
            oid = order_id()
            new_order = {
                "id": oid,
                "sender_id": sender_id,
                "name": cart["name"],
                "phone": cart["phone"],
                "address": cart["address"],
                "items": cart["items"],
                "subtotal": cart["total"] - cart["fee"],
                "delivery_fee": cart["fee"],
                "delivery_zone": cart["zone"],
                "total": cart["total"],
                "status": "confirmed",
                "payment_status": "pending",
                "created_at": now_str(),
                "courier_tracking": ""
            }
            client_config.setdefault("orders", []).append(new_order)
            update_client(page_id, client_config)
            cart.update({"items": [], "state": STATES["DONE"]})

            bkash_number = client_config.get("apiKeys", {}).get("bkashNumber", "")
            payment_msg = (f"\n\n💳 পেমেন্টের জন্য bKash করুন: {bkash_number}\n"
                           f"পেমেন্ট রেফারেন্স নম্বর পাঠান।") if bkash_number else ""

            fb_send(sender_id,
                f"✅ অর্ডার কনফার্ম হয়েছে!\n"
                f"অর্ডার ID: {oid}\n"
                f"মোট: ৳{cart['total']}{payment_msg}\n\n"
                f"ডেলিভারি পাওয়ার পর জানাবেন। ধন্যবাদ! 🎉",
                access_token)
            return
        else:
            cart.update({"items": [], "state": STATES["BROWSING"]})
            fb_send(sender_id, "অর্ডার বাতিল। আবার অর্ডার করতে পণ্যের নাম লিখুন।", access_token)
            return

    # ── Hold cart ──
    if has_trigger(msg, HOLD_TRIGGERS) and cart["items"]:
        cart["hold_until"] = time.time() + 7200  # 2 hours
        cart["state"] = STATES["HOLD"]
        fb_send(sender_id, "✅ ২ ঘণ্টার জন্য হোল্ড করা হয়েছে। এর মধ্যে checkout না করলে অটো release হয়ে যাবে।", access_token)
        return

    # ── Proceed to checkout ──
    if has_trigger(msg, DONE_TRIGGERS) and cart["items"] and state != STATES["BROWSING"]:
        cart["state"] = STATES["CHECKOUT"]
        fb_send(sender_id, f"চমৎকার! আপনার কার্টে আছে:\n{cart_summary(cart)}\n\nআপনার পুরো নাম দিন:", access_token)
        return

    # ── Add to cart (order intent) ──
    if has_trigger(msg, ORDER_TRIGGERS):
        # Try to extract product from message
        matches = []
        for p in inventory:
            if p.get("name","").lower() in msg.lower() or any(w in p.get("name","").lower() for w in msg.lower().split()):
                matches.append(p)

        if not matches:
            # Show product list
            avail = [p for p in inventory if p.get("stock",0) > 0]
            if avail:
                prod_list = "\n".join([f"• {p['name']} — ৳{p['price']}" for p in avail[:10]])
                fb_send(sender_id,
                    f"কোন পণ্যটি নিতে চান? আমাদের কাছে আছে:\n\n{prod_list}\n\nপণ্যের নাম লিখুন।",
                    access_token)
            else:
                fb_send(sender_id, "দুঃখিত, এই মুহূর্তে কোনো পণ্য স্টকে নেই।", access_token)
            return

        # Extract quantity
        qty_match = re.search(r"(\d+)\s*(টা|টি|pcs|pieces|pc|pair|পিস|জোড়া)?", msg)
        qty = int(qty_match.group(1)) if qty_match else 1

        product = matches[0]
        if product.get("stock", 0) <= 0:
            fb_send(sender_id, f"দুঃখিত, {product['name']} এই মুহূর্তে স্টকে নেই।", access_token)
            return

        # Check if already in cart
        existing = next((i for i in cart["items"] if i["name"] == product["name"]), None)
        if existing:
            existing["qty"] += qty
        else:
            cart["items"].append({"name": product["name"], "price": product["price"], "qty": qty})

        cart["state"] = STATES["ADDING"]
        subtotal = sum(int(i["price"])*i["qty"] for i in cart["items"])
        fb_send(sender_id,
            f"✅ কার্টে যোগ হয়েছে: {product['name']} × {qty} — ৳{int(product['price'])*qty}\n"
            f"কার্ট মোট: ৳{subtotal}\n\n"
            f"আরো পণ্য যোগ করুন, অথবা 'done' বলুন checkout করতে।",
            access_token)
        return

    # ── Default: AI reply ──
    reply = ai_reply(msg, client_config)
    fb_send(sender_id, reply, access_token)

# ─── Abandoned cart recovery (called by scheduler / cron) ────
def check_abandoned_carts():
    """Called periodically — sends reminders for carts idle 2h and 24h."""
    now = time.time()
    clients = get_clients()
    for page_id, carts_for_page in carts.items():
        client = clients.get(page_id)
        if not client:
            continue
        for sender_id, cart in carts_for_page.items():
            if not cart["items"] or cart["state"] in [STATES["BROWSING"], STATES["DONE"]]:
                continue
            idle = now - cart.get("last_active", now)
            if 7000 < idle < 7400:  # ~2 hours
                fb_send(sender_id,
                    "🛒 আপনার কার্টে পণ্য আছে! অর্ডার কমপ্লিট করতে 'done' লিখুন।",
                    client["access_token"])
            elif 86000 < idle < 86400:  # ~24 hours
                fb_send(sender_id,
                    "🎁 কাল আপনি কিছু দেখেছিলেন কিন্তু অর্ডার করেননি। আজই অর্ডার করুন — স্টক সীমিত!",
                    client["access_token"])

# ─── bKash transaction detection ─────────────────────────────
def check_bkash_payment(sender_id, msg, client_config, page_id):
    """Detect bKash/Nagad transaction ID patterns in messages."""
    # bKash TrxID pattern: 10 alphanumeric chars, often starts with letter
    trx_pattern = r"\b([A-Z0-9]{8,12})\b"
    match = re.search(trx_pattern, msg.upper())
    if not match:
        return False

    trx_id = match.group(1)
    # Find pending order for this sender
    orders = client_config.get("orders", [])
    for order in orders:
        if order.get("sender_id") == sender_id and order.get("payment_status") == "pending":
            order["payment_status"] = "paid"
            order["transaction_id"] = trx_id
            order["paid_at"] = now_str()
            update_client(page_id, client_config)
            fb_send(sender_id,
                f"✅ পেমেন্ট রেকর্ড করা হয়েছে!\nTrx ID: {trx_id}\nঅর্ডার: {order['id']}\n"
                f"আপনার পণ্য শীঘ্রই পাঠানো হবে। 🚀",
                client_config["access_token"])
            return True
    return False

# ═══════════════════════════════════════════════════════════════
# FACEBOOK WEBHOOK
# ═══════════════════════════════════════════════════════════════
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        verify = os.environ.get("VERIFY_TOKEN", "alap_verify_token")
        if token == verify:
            return challenge, 200
        return "Invalid token", 403

    body = request.get_json(silent=True) or {}

    for entry in body.get("entry", []):
        page_id = str(entry.get("id", ""))
        clients_map = get_clients()
        client_config = clients_map.get(page_id)

        if not client_config:
            # Try Instagram / unknown — skip
            continue

        # ── Facebook Messenger DM ──
        for event in entry.get("messaging", []):
            sender_id = event.get("sender", {}).get("id", "")
            msg_obj = event.get("message", {})
            message = msg_obj.get("text", "").strip()

            if not message or sender_id == page_id:
                continue

            # Check if bKash TrxID
            if check_bkash_payment(sender_id, message, client_config, page_id):
                continue

            handle_message(sender_id, message, client_config, page_id)

        # ── Facebook Comment webhook ──
        for change in entry.get("changes", []):
            val = change.get("value", {})
            if change.get("field") == "feed" and val.get("item") == "comment":
                handle_comment_to_dm(val, client_config, page_id)

    return "OK", 200

# ─── Comment-to-DM ───────────────────────────────────────────
def handle_comment_to_dm(val, client_config, page_id):
    """When someone comments on a post, send them a DM."""
    commenter_id = val.get("from", {}).get("id")
    comment_text = val.get("message", "")
    post_id = val.get("post_id", "")

    if not commenter_id or commenter_id == page_id:
        return

    trigger_keywords = client_config.get("comment_triggers", ["price", "দাম", "কত", "how much", "available", "আছে"])

    if not any(kw.lower() in comment_text.lower() for kw in trigger_keywords):
        return

    access_token = client_config["access_token"]

    # Log this lead
    client_config.setdefault("leads", []).append({
        "sender_id": commenter_id,
        "source": "comment",
        "comment": comment_text,
        "post_id": post_id,
        "created_at": now_str(),
        "status": "new"
    })
    update_client(page_id, client_config)

    avail = [p for p in client_config.get("inventory", []) if p.get("stock", 0) > 0]
    prod_list = "\n".join([f"• {p['name']} — ৳{p['price']}" for p in avail[:5]])

    fb_send(commenter_id,
        f"হ্যালো! আপনার মন্তব্যের জন্য ধন্যবাদ 😊\n\n"
        f"আমাদের পণ্যসমূহ:\n{prod_list}\n\n"
        f"অর্ডার করতে পণ্যের নাম লিখুন।",
        access_token)

# ═══════════════════════════════════════════════════════════════
# CLIENT PANEL API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

def auth(req):
    """Validate panel_token from request header."""
    token = req.headers.get("X-Panel-Token", "")
    return get_client_by_token(token)

# ── Sync: Pull orders + leads + stats for the panel ──────────
@app.route("/api/sync", methods=["POST"])
def api_sync():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "orders":        client.get("orders", []),
        "leads":         client.get("leads", []),
        "urgent_chats":  client.get("urgent_chats", []),
        "inventory":     client.get("inventory", []),
        "blacklist":     client.get("blacklist", []),
    })

# ── Orders ───────────────────────────────────────────────────
@app.route("/api/orders", methods=["GET"])
def api_orders():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(client.get("orders", []))

@app.route("/api/orders/<order_id>/status", methods=["POST"])
def api_update_order(order_id):
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    body = request.get_json() or {}
    new_status = body.get("status")
    for order in client.get("orders", []):
        if order["id"] == order_id:
            order["status"] = new_status
            order["updated_at"] = now_str()
            update_client(client["page_id"], client)
            # Notify customer
            if new_status == "delivered":
                fb_send(order["sender_id"],
                    f"🎉 আপনার পণ্য ডেলিভার হয়েছে!\nঅর্ডার: {order_id}\nধন্যবাদ!",
                    client["access_token"])
            return jsonify({"ok": True})
    return jsonify({"error": "Order not found"}), 404

# ── Courier booking (server-side, no CORS issues) ────────────
@app.route("/api/book-courier", methods=["POST"])
def api_book_courier():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json() or {}
    order_id_val = body.get("order_id")
    courier = body.get("courier", "steadfast")  # "steadfast" or "pathao"

    order = next((o for o in client.get("orders", []) if o["id"] == order_id_val), None)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    api_keys = client.get("apiKeys", {})

    if courier == "steadfast":
        result = book_steadfast(order, api_keys)
    elif courier == "pathao":
        result = book_pathao(order, api_keys)
    else:
        return jsonify({"error": "Unknown courier"}), 400

    if result.get("success"):
        order["courier"] = courier
        order["courier_tracking"] = result.get("tracking_code", "")
        order["courier_consignment"] = result.get("consignment_id", "")
        order["status"] = "dispatched"
        order["dispatched_at"] = now_str()
        update_client(client["page_id"], client)
        # Notify customer
        fb_send(order["sender_id"],
            f"📦 আপনার পণ্য পাঠানো হয়েছে!\n"
            f"ট্র্যাকিং: {result.get('tracking_code','')}\n"
            f"কুরিয়ার: {courier.title()}",
            client["access_token"])
    return jsonify(result)

def book_steadfast(order, api_keys):
    key = api_keys.get("steadfastKey", "")
    secret = api_keys.get("steadfastSecret", "")
    if not key or not secret:
        return {"success": False, "error": "Steadfast API key/secret not configured"}
    try:
        resp = requests.post(
            "https://portal.packzy.com/api/v1/create_order",
            headers={"Api-Key": key, "Secret-Key": secret, "Content-Type": "application/json"},
            json={
                "invoice": order["id"],
                "recipient_name": order["name"],
                "recipient_phone": order["phone"],
                "recipient_address": order["address"],
                "cod_amount": order["total"],
                "note": f"Alap order {order['id']}"
            },
            timeout=15
        )
        data = resp.json()
        if resp.status_code in [200, 201] and data.get("status") in [200, 201]:
            consignment = data.get("consignment", {})
            return {
                "success": True,
                "tracking_code": consignment.get("tracking_code", ""),
                "consignment_id": str(consignment.get("id", "")),
                "courier": "Steadfast"
            }
        return {"success": False, "error": data.get("message", "Steadfast error")}
    except Exception as e:
        return {"success": False, "error": str(e)}

def book_pathao(order, api_keys):
    client_id     = api_keys.get("pathaoClientId", "")
    client_secret = api_keys.get("pathaoClientSecret", "")
    username      = api_keys.get("pathaoUsername", "")
    password      = api_keys.get("pathaoPassword", "")
    store_id      = api_keys.get("pathaoStoreId", "")

    if not all([client_id, client_secret, username, password, store_id]):
        return {"success": False, "error": "Pathao credentials incomplete"}

    try:
        # Step 1: Get access token
        token_resp = requests.post(
            "https://api-hermes.pathao.com/aladdin/api/v1/issue-token",
            json={"client_id": client_id, "client_secret": client_secret,
                  "username": username, "password": password,
                  "grant_type": "password"},
            timeout=15
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return {"success": False, "error": "Pathao auth failed: " + str(token_data)}

        # Step 2: Create order
        order_resp = requests.post(
            "https://api-hermes.pathao.com/aladdin/api/v1/orders",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={
                "store_id":            int(store_id),
                "merchant_order_id":   order["id"],
                "recipient_name":      order["name"],
                "recipient_phone":     order["phone"],
                "recipient_address":   order["address"],
                "recipient_city":      1,   # 1=Dhaka
                "recipient_zone":      1,
                "delivery_type":       48,  # 48h delivery
                "item_type":           2,
                "special_instruction": "",
                "item_quantity":       sum(i["qty"] for i in order["items"]),
                "item_weight":         0.5,
                "amount_to_collect":   order["total"],
                "item_description":    ", ".join(i["name"] for i in order["items"])
            },
            timeout=15
        )
        resp_data = order_resp.json()
        if order_resp.status_code in [200, 201]:
            payload = resp_data.get("data", {})
            return {
                "success": True,
                "tracking_code": payload.get("order_status", ""),
                "consignment_id": str(payload.get("order_id", "")),
                "courier": "Pathao"
            }
        return {"success": False, "error": str(resp_data)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── Paperfly courier ──────────────────────────────────────────
def book_paperfly(order, api_keys):
    key = api_keys.get("paperflyKey", "")
    secret = api_keys.get("paperflySecret", "")
    if not key or not secret:
        return {"success": False, "error": "Paperfly credentials not configured"}
    try:
        credentials = base64.b64encode(f"{key}:{secret}".encode()).decode()
        resp = requests.post(
            "https://api.paperfly.com.bd/api/order/send",
            headers={"Authorization": f"Basic {credentials}", "Content-Type": "application/json"},
            json={
                "merchant_order_id": order["id"],
                "customer_name":     order["name"],
                "customer_phone":    order["phone"],
                "delivery_address":  order["address"],
                "cod_amount":        order["total"],
                "product_description": ", ".join(i["name"] for i in order["items"])
            },
            timeout=15
        )
        data = resp.json()
        if resp.status_code in [200, 201]:
            return {
                "success": True,
                "tracking_code": data.get("tracking_id", data.get("tracking", "")),
                "consignment_id": str(data.get("order_id", "")),
                "courier": "Paperfly"
            }
        return {"success": False, "error": str(data)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ── WhatsApp Broadcast ────────────────────────────────────────
@app.route("/api/broadcast", methods=["POST"])
def api_broadcast():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json() or {}
    message = body.get("message", "")
    recipients = body.get("recipients", [])  # list of phone numbers
    wa_token = client.get("apiKeys", {}).get("whatsappToken", "")
    wa_phone_id = client.get("apiKeys", {}).get("whatsappPhoneId", "")

    if not wa_token or not wa_phone_id:
        return jsonify({"error": "WhatsApp credentials not configured"}), 400

    sent, failed = 0, 0
    for phone in recipients:
        phone = re.sub(r"[^\d]", "", phone)
        if not phone.startswith("880"):
            phone = "880" + phone.lstrip("0")
        try:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{wa_phone_id}/messages",
                headers={"Authorization": f"Bearer {wa_token}", "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "to": phone,
                      "type": "text", "text": {"body": message}},
                timeout=10
            )
            if resp.status_code == 200:
                sent += 1
            else:
                failed += 1
        except Exception:
            failed += 1

    return jsonify({"sent": sent, "failed": failed})

# ── OCR Invoice Scanner ───────────────────────────────────────
@app.route("/api/ocr-scan", methods=["POST"])
def api_ocr_scan():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json() or {}
    image_b64 = body.get("image")  # base64 encoded image
    vision_key = client.get("apiKeys", {}).get("googleVisionKey", "")

    if not vision_key:
        return jsonify({"error": "Google Vision API key not configured"}), 400
    if not image_b64:
        return jsonify({"error": "No image provided"}), 400

    try:
        resp = requests.post(
            f"https://vision.googleapis.com/v1/images:annotate?key={vision_key}",
            json={"requests": [{"image": {"content": image_b64},
                                "features": [{"type": "TEXT_DETECTION", "maxResults": 1}]}]},
            timeout=20
        )
        data = resp.json()
        full_text = data["responses"][0].get("fullTextAnnotation", {}).get("text", "")

        # Parse product lines: look for patterns like "Product Name  qty  price"
        products = parse_invoice_text(full_text)
        return jsonify({"text": full_text, "products": products})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def parse_invoice_text(text):
    """Basic heuristic to extract product rows from OCR text."""
    products = []
    for line in text.split("\n"):
        # Skip short/header lines
        if len(line.strip()) < 3:
            continue
        # Look for price pattern: number possibly with ৳
        price_match = re.search(r"[৳\$]?\s*(\d+(?:\.\d+)?)", line)
        qty_match   = re.search(r"\b(\d+)\s*(pcs|pairs|টি|টা|piece|pair)\b", line, re.IGNORECASE)

        if price_match:
            name_part = line[:price_match.start()].strip(" -|:") or "Product"
            products.append({
                "name":  name_part[:40],
                "price": price_match.group(1),
                "stock": int(qty_match.group(1)) if qty_match else 0,
                "details": ""
            })
    return products[:30]

# ── Profit Tracker ────────────────────────────────────────────
@app.route("/api/profit", methods=["GET"])
def api_profit():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    orders = [o for o in client.get("orders", []) if o.get("status") not in ["cancelled"]]
    expenses = client.get("expenses", [])

    gross_revenue  = sum(o.get("total", 0) for o in orders)
    delivery_income = sum(o.get("delivery_fee", 0) for o in orders)
    total_expenses = sum(e.get("amount", 0) for e in expenses)
    net_profit     = gross_revenue - total_expenses

    # By month
    monthly = {}
    for o in orders:
        month = o.get("created_at", "")[:7]  # "2025-06"
        monthly.setdefault(month, {"revenue": 0, "orders": 0})
        monthly[month]["revenue"] += o.get("total", 0)
        monthly[month]["orders"]  += 1

    return jsonify({
        "gross_revenue":   gross_revenue,
        "delivery_income": delivery_income,
        "total_expenses":  total_expenses,
        "net_profit":      net_profit,
        "order_count":     len(orders),
        "monthly":         monthly,
        "expenses":        expenses
    })

# ── Log Expense ───────────────────────────────────────────────
@app.route("/api/expenses", methods=["POST"])
def api_log_expense():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    body = request.get_json() or {}
    expense = {
        "id":          uuid.uuid4().hex[:8],
        "description": body.get("description", ""),
        "amount":      float(body.get("amount", 0)),
        "category":    body.get("category", "Other"),
        "date":        now_str()
    }
    client.setdefault("expenses", []).append(expense)
    update_client(client["page_id"], client)
    return jsonify({"ok": True, "expense": expense})

# ── Blacklist ─────────────────────────────────────────────────
@app.route("/api/blacklist", methods=["GET", "POST", "DELETE"])
def api_blacklist():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == "GET":
        return jsonify(client.get("blacklist", []))

    body = request.get_json() or {}

    if request.method == "POST":
        phone = re.sub(r"[^\d+]", "", body.get("phone", ""))
        if not phone:
            return jsonify({"error": "Phone required"}), 400
        bl = client.setdefault("blacklist", [])
        if not any(b["phone"] == phone for b in bl):
            bl.append({"phone": phone, "reason": body.get("reason", ""), "added_at": now_str()})
            update_client(client["page_id"], client)
        return jsonify({"ok": True})

    if request.method == "DELETE":
        phone = body.get("phone", "")
        client["blacklist"] = [b for b in client.get("blacklist", []) if b["phone"] != phone]
        update_client(client["page_id"], client)
        return jsonify({"ok": True})

# ── Facebook Lead Form webhook ────────────────────────────────
@app.route("/webhook/leads", methods=["POST"])
def webhook_leads():
    """Receives Meta Lead Form submissions."""
    body = request.get_json(silent=True) or {}
    for entry in body.get("entry", []):
        page_id = str(entry.get("id", ""))
        clients_map = get_clients()
        client_config = clients_map.get(page_id)
        if not client_config:
            continue
        for change in entry.get("changes", []):
            val = change.get("value", {})
            if change.get("field") == "leadgen":
                lead_id = val.get("leadgen_id")
                # Fetch lead data from Graph API
                try:
                    r = requests.get(
                        f"https://graph.facebook.com/v18.0/{lead_id}",
                        params={"access_token": client_config["access_token"],
                                "fields": "field_data,created_time"},
                        timeout=10
                    )
                    lead_data = r.json()
                    fields = {f["name"]: f["values"][0] for f in lead_data.get("field_data", [])}
                    client_config.setdefault("leads", []).append({
                        "source": "lead_form",
                        "name": fields.get("full_name", ""),
                        "phone": fields.get("phone_number", ""),
                        "email": fields.get("email", ""),
                        "created_at": now_str(),
                        "status": "new"
                    })
                    update_client(page_id, client_config)
                    # Send welcome DM if PSID known (not always possible)
                except Exception as e:
                    print(f"Lead fetch error: {e}")
    return "OK", 200

# ── Inventory sync from panel ─────────────────────────────────
@app.route("/api/inventory", methods=["POST"])
def api_update_inventory():
    client = auth(request)
    if not client:
        return jsonify({"error": "Unauthorized"}), 401
    body = request.get_json() or {}
    client["inventory"] = body.get("inventory", client.get("inventory", []))
    update_client(client["page_id"], client)
    return jsonify({"ok": True})

# ── Health check ──────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Alap Bot running", "version": "2.0"})

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
