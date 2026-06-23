# Alap Client Panel v3 — Stock Management & Q&A Learning Guide

## 🎯 What's New?

### 1. **Stock Management** (Actual Numbers, Not Just Yes/No)
- Track how many pieces you have
- Update stock as you sell
- Live dashboard shows stock alerts

### 2. **Live Dashboard** (Real-Time View)
- See all products at a glance
- Stock status: In Stock / Low Stock / Out of Stock
- Quick stats: Total products, in stock, low stock

### 3. **Customer Q&A Learning** (Bot Gets Smarter)
- Share customer questions with the bot
- Bot learns your answers
- Repeats same answers to similar future questions

---

## 📊 Three Main Sections

### Section 1: Live Dashboard
**What:** Real-time view of your entire inventory
**Shows:**
- Total products count
- How many are in stock
- How many are low stock (≤5 pieces)
- Full product list with live stock levels
- Stock alerts for products running low

**Why it's useful:**
- Check inventory without opening full management
- See what's running out
- Plan restocking

---

### Section 2: Manage Inventory
**What:** Add, edit, delete products & upload Excel
**Features:**
- **Add Product**: Click button → Enter name, price, size, stock amount
- **Edit Product**: Change any detail
- **Delete Product**: Remove product
- **Update Stock**: Click directly in stock column to update as you sell
- **Upload Excel**: Bulk import with columns: Name, Price, Size, Stock
- **Download JSON**: Backup your data

**Stock Amount**
- Enter actual number: 5, 10, 25, etc.
- Customer doesn't see this number
- Bot checks: if stock > 0 → "yes", if stock = 0 → "no"

---

### Section 3: Customer Q&A Training
**What:** Teach the bot customer questions and your answers

**Two Ways to Add Q&A:**

#### Option A: Extract from Text (AI-Powered)
```
Paste this:
"Customer asked: Do you deliver outside Dhaka?
I answered: Yes, we deliver everywhere in Bangladesh"

Click: Extract Q&A from Text

Bot extracts:
Q: Do you deliver outside Dhaka?
A: Yes, we deliver everywhere in Bangladesh
```

#### Option B: Add Manually
```
Q: What's your delivery time?
A: 1-2 days inside Dhaka, 3-5 days outside

Click: Add Q&A
```

---

## 🔄 How Stock Management Works

### For Clients (Your Side)

**Day 1: Add Products**
```
Sharee - Price: 1200, Stock: 10
Salwar - Price: 1500, Stock: 5
Panjabi - Price: 900, Stock: 15
```

**Day 2: Customer Buys 3 Sharees**
```
Update stock: 10 → 7
(Click on stock number, type 7)
Dashboard shows: ✓ 7 pieces
```

**Day 5: Running Low!**
```
Dashboard shows: ⚠ Low Stock Alert
Salwar only has 2 pieces left
Panjabi down to 8
→ Time to restock!
```

### For Bot (Customer Side)

**What Bot Knows:**
```
Sharee: 7 pieces in stock ← INTERNAL (don't show)
Salwar: 2 pieces in stock ← INTERNAL (don't show)
Panjabi: 8 pieces in stock ← INTERNAL (don't show)
```

**What Bot Tells Customer:**
```
Customer: Do you have Sharee?
Bot: "Yes! We have Sharee for ৳1200 (Cotton M/L)"
     ← Doesn't say "7 pieces"

Customer: Is Salwar available?
Bot: "Sorry, Salwar is currently out of stock"
     ← Knows it has only 2 left (low) but says "out"
     ← Or could say "Yes, we have 1 left" (your choice in Q&A)
```

**Logic:**
- `stock > 0` → Say "Yes, we have it"
- `stock = 0` → Say "Sorry, out of stock"
- Never mention exact numbers to customers

---

## 🤖 How Q&A Learning Works

### Client-Side: Adding Q&A

**Scenario 1: Customer Asks via WhatsApp**
```
Customer: "How much is delivery?"
You: "80 taka inside Dhaka, 150 outside"

→ Copy this conversation
→ Paste in "Add Customer Q&A"
→ Click "Extract Q&A from Text"
→ AI pulls out:
   Q: How much is delivery?
   A: 80 taka inside Dhaka, 150 outside
```

**Scenario 2: Customer Asks on Facebook**
```
Same process!
Copy their message + your reply
Paste → Extract → Done
```

**Scenario 3: Manual Add (No Copy-Paste)**
```
Q: Do you accept cash on delivery?
A: Yes, we accept cash on delivery
Click: Add Q&A
```

### Bot-Side: Using Q&A

**Before Q&A Training:**
```
Customer: Do you deliver outside Dhaka?
Bot: "Yes! We deliver all over Bangladesh"
     (Generic answer from AI guessing)
```

**After Q&A Training (You Added Answer):**
```
Customer: Do you deliver outside Dhaka?
Bot: "Yes, we deliver everywhere in Bangladesh"
     (Uses YOUR exact answer from Q&A)
```

**Why This Matters:**
- Bot sounds like you (consistent voice)
- Your real answers, not AI guessing
- Customers get accurate info

---

## 📋 JSON Format (What Gets Stored)

### New Format with Stock & Q&A

```json
{
  "pages": [
    {
      "page_id": "132435660741702",
      "business_name": "Crafts and Gifts BD",
      "access_token": "EAAxxxxx...",
      "status": "active",
      "inventory": [
        {
          "name": "Sharee",
          "price": "1200",
          "details": "Cotton M/L",
          "stock": 7
        },
        {
          "name": "Salwar",
          "price": "1500",
          "details": "Silk M/L",
          "stock": 2
        }
      ],
      "qa": [
        {
          "q": "How much is delivery?",
          "a": "80 taka inside Dhaka, 150 outside"
        },
        {
          "q": "Do you accept cash on delivery?",
          "a": "Yes, we accept cash on delivery"
        }
      ]
    }
  ]
}
```

---

## ⚙️ Bot Code Changes

### Updated app.py (Flask)

Your bot needs to handle:
1. **Stock checking** (internal only, don't tell customers exact amounts)
2. **Q&A usage** (use your answers in bot responses)
3. **New JSON format** (read `inventory[].stock` and `qa[]`)

**Key Changes:**

**Before:**
```python
# Bot knew: Available = Yes/No
product["available"]  # True or False
```

**After:**
```python
# Bot knows: Exact stock amount
product["stock"]      # 0, 5, 10, 25, etc.

# Bot checks:
if product["stock"] > 0:
    tell_customer = "Yes"
else:
    tell_customer = "No"
```

**Q&A Usage:**

```python
def get_qa_context(qa_list):
    """Add Q&A to bot knowledge"""
    context = "Known answers:\n"
    for item in qa_list:
        context += f"Q: {item['q']}\nA: {item['a']}\n"
    return context

# Use in AI prompt:
prompt += get_qa_context(client["qa"])
```

---

## 🚀 Workflow: Everything Together

### Day 1: Setup
```
1. Open Client Panel v3
2. Login with token
3. Go to "Manage Inventory"
4. Upload Excel with products + stock amounts
5. Go to "Customer Q&A"
6. Add 5-10 common Q&A from past customers
7. Download JSON
8. Push to GitHub → Railway deploys
```

### Day 2-7: Daily Operations
```
1. Check "Live Dashboard" each morning
2. See what's running low
3. Update stock as you sell (click to edit)
4. When customers ask new questions → Add to Q&A section
5. Download JSON (end of day or weekly)
6. Push to GitHub
```

### Week 2+: Bot Gets Better
```
- More Q&A added = bot answers improve
- Bot sounds like you (your words)
- Customer questions answered faster
- Less support burden
```

---

## 📊 Stock Status Levels

| Stock | Status | Badge | Shows to Customer |
|-------|--------|-------|------------------|
| > 5 | In Stock | ✓ Green | "Yes, we have it" |
| 1-5 | Low Stock | ⚠ Orange | "Yes, we have it" (or "Only X left" in Q&A) |
| 0 | Out of Stock | ✗ Red | "Sorry, out of stock" |

---

## 💡 Best Practices

### For Stock Management
✅ **Update regularly** — Update stock after each sale
✅ **Set alerts** — Dashboard warns when low
✅ **Batch uploads** — Use Excel for big restocks
✅ **Download backups** — JSON backup weekly

❌ **Don't** add stock amounts higher than realistic
❌ **Don't** leave stock at 999 (be accurate)

### For Q&A Learning
✅ **Save real conversations** — Use actual customer questions
✅ **Be specific** — Your exact answers matter
✅ **Update regularly** — Add 2-3 per week
✅ **Group similar** — "Do you deliver?" and "Delivery outside Dhaka?" separately

❌ **Don't** invent Q&A (use real ones)
❌ **Don't** make answers too long (keep under 2 sentences)

---

## 🔒 Privacy Note: Stock Amounts

**Stored:** Stock amounts saved in JSON (internal only)
**Shown to Customers:** Just "Available" or "Out of Stock"
**Why:** Psychological pricing - customers don't see you're running low

---

## 📥 Excel Template

When uploading inventory:

```
Name      | Price | Size/Details    | Stock
----------|-------|-----------------|-------
Sharee    | 1200  | Cotton M/L     | 7
Salwar    | 1500  | Silk M/L       | 2
Panjabi   | 900   | Cotton M       | 15
Dupatta   | 300   | Pure cotton    | 20
```

---

## 🎓 Example Workflow

### Week 1
```
Monday:
- Add 10 products with stock
- Add 5 common Q&A
- Push JSON to bot

Tuesday-Friday:
- Dashboard shows Dupatta running low
- Update stock: 20 → 15 → 10 → 5
- Alert: "Low Stock - Only 5 Dupattas left"

Sunday:
- Restock Dupatta: 5 → 50
- Download JSON
- Push update
```

---

## ❓ FAQ

**Q: Can I update stock without downloading JSON every time?**
A: For small updates (1-2 changes), just update in panel. For bulk/daily, download once per day.

**Q: What if customer asks about stock?**
A: Bot doesn't reveal exact numbers. Use Q&A section to set your policy:
- Q: "How many do you have left?"
- A: "We have limited stock. Hurry before it runs out!" (vague intentional)

**Q: Can bot access Q&A from old conversations?**
A: Only what you add to "Customer Q&A" section. Previous messages not auto-imported.

**Q: What if I make a mistake in stock number?**
A: Just click and update. Changes save instantly.

**Q: Stock gets out of sync with actual sales?**
A: Keep updating as you sell. Or weekly reconciliation.

---

## 🔄 Version Comparison

| Feature | v1 (Original) | v2 (AI) | v3 (Stock + Q&A) |
|---------|---------------|---------|-----------------|
| Manual entry | ✓ | ✓ | ✓ |
| AI commands | ✗ | ✓ | ✓ |
| Stock tracking | Just Yes/No | Just Yes/No | **Numbers** |
| Live dashboard | ✗ | ✗ | **✓** |
| Q&A learning | ✗ | ✗ | **✓** |
| Stock alerts | ✗ | ✗ | **✓** |

---

## 📚 Files You Need

1. **Alap_Client_Panel_v3.html** ← Use this (NEW)
2. **Alap_Admin_Panel_v2.html** ← Same as before
3. **Updated app.py** ← Update your Flask bot with this code

---

**Version:** Alap Client Panel v3.0  
**Status:** Production Ready ✅  
**Last Updated:** June 2025
