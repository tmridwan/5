# Alap — Complete Two-Sided System Guide

Welcome! You now have a **complete system** with:
- **Admin Panel** (for you) — manage all clients
- **Client Panel** (for your customers) — edit their own inventory
- **History Tracking** — audit trail of all changes
- **Excel Import** — bulk upload products
- **Text Commands** — quick product entry
- **Auto-generated Tokens** — secure client access

---

## 📦 What You Have

### 1. Alap_Admin_Panel_v2.html
**Your control center** — manage everything

**Features:**
- Dashboard with stats (total clients, revenue, new signups)
- Add new clients (creates unique token automatically)
- View all clients and their tokens
- Export customers.json for Flask server
- Export client list as CSV
- Manage access tokens
- Generate and revoke client tokens

**How it works:**
- Open in browser (no server needed)
- Data stored in localStorage (local to your computer)
- When you add a client, a random token is generated: `alap_token_x7k9p2m1`
- Share this token with the client

---

### 2. Alap_Client_Panel.html
**Your customer's dashboard** — edit inventory themselves

**Features:**
- Login with Business Name + Token (you provide the token)
- Add/edit/delete products manually
- Upload Excel file (auto-converts to JSON)
- Type text commands: `Sharee 1200 Cotton M/L Yes`
- View complete change history with timestamps
- Download their inventory as JSON backup
- Change audit log (see who changed what and when)

**How it works:**
- Each client gets the same HTML file
- They login with their unique token
- All data stored in browser localStorage
- Each client can only see their own inventory

---

### 3. customers.json
**For your Flask server on Railway**

This file contains all clients' data:
```json
{
  "pages": [
    {
      "page_id": "132435660741702",
      "access_token": "EAAxxxxx...",
      "business_name": "Crafts and Gifts BD",
      "language": "bangla_english",
      "status": "active",
      "inventory": [...],
      "history": [...]
    }
  ]
}
```

---

## 🚀 Step-by-Step Setup

### Phase 1: Initial Setup (Today)

**Step 1 — Open Admin Panel**
```
1. Download: Alap_Admin_Panel_v2.html
2. Open in browser
3. You'll see empty dashboard
```

**Step 2 — Add First Client**
```
1. Click "Add Client" button
2. Fill in:
   - Business Name: "Crafts and Gifts BD"
   - Page ID: 132435660741702
   - Access Token: [from Meta Developer]
   - Monthly Fee: 2500
   - Status: Active
3. Click "Create Client & Generate Token"
4. System generates: alap_token_x7k9p2m1
```

**Step 3 — View the Token**
```
1. Click "Access Tokens" in sidebar
2. See your client + their token
3. Copy the token to clipboard
```

**Step 4 — Share with Client**
Send email:
```
Hi [Client Name],

You can now manage your inventory on Alap!

1. Download this file: Alap_Client_Panel.html
2. Open it in your browser
3. Enter:
   - Business Name: Crafts and Gifts BD
   - Token: alap_token_x7k9p2m1
4. You can now add/edit products!

Questions? Reply here.
```

**Step 5 — Export customers.json**
```
1. In Admin Panel, click Settings
2. Click "Export customers.json"
3. File downloads to your computer
4. Copy it to your project folder
5. Push to GitHub:
   git add customers.json
   git commit -m "add alap clients"
   git push
6. Railway deploys automatically (60 seconds)
```

---

### Phase 2: Client Uses the System (Week 1)

**Client Login**
```
1. Open Alap_Client_Panel.html (you sent this file)
2. Enters Business Name + Token
3. Clicks Sign In
4. Now in their dashboard
```

**Client Adds Products — Method 1: Manual**
```
1. Click "+ Add Product"
2. System shows empty row
3. Click "Edit" on that row
4. Popup appears for each field
5. Enter: Name, Price, Size/Details, Available (Yes/No)
6. Save
7. Product added + History recorded
```

**Client Adds Products — Method 2: Excel**
```
1. Prepare Excel file with columns:
   Name | Price | Size/Details | Available
   
2. In Client Panel, click "Browse"
3. Select Excel file
4. File uploads
5. All products imported instantly
6. History shows: "Imported 15 products from Excel"
```

**Client Adds Products — Method 3: Text Command**
```
1. At bottom, see text input
2. Type: Sharee 1200 Cotton M/L Yes
3. Click Add
4. Product appears in table
5. Format: ProductName Price Details Available
```

**Client Views History**
```
1. Click "Change History" tab
2. See every change:
   - Added Sharee (৳1200) — Edit
   - Imported 15 products from Excel — Import
   - Updated Sharee to Sharee Green — Edit
   - Deleted Salwar — Delete
3. Timestamp for each change
4. Color-coded by action type
```

---

### Phase 3: Sync to Your Server (End of Week)

**Client Downloads Their JSON**
```
1. Client clicks "Download JSON"
2. Gets file: Crafts_and_Gifts_BD_inventory.json
3. This is their current inventory
4. Can save as backup
```

**You Update Your System**
```
1. In Admin Panel, go to Settings
2. Click "Export customers.json"
3. This includes ALL clients' current inventory
4. Their JSON = what Admin exported
5. Push to GitHub again
6. Railway reads updated customers.json
7. Bot now uses their latest inventory
```

**New DM = Bot Replies**
```
Customer: "Do you have sharee?"
Bot (reads inventory): "Yes! We have Sharee for ৳1200..."
```

---

## 🔑 Understanding Tokens

### What is a Token?
A unique password that gives a client access to edit **only their own** inventory.

**Example:**
- Token for "Crafts and Gifts BD": `alap_token_x7k9p2m1`
- Token for "Fashion Store": `alap_token_a3k2p8n5`

Each token gives access to ONE business only.

### How to Generate Tokens

**Automatic (Recommended):**
1. Add client in Admin Panel
2. System auto-generates random token
3. Copy and send to client

**Manual (if needed):**
You can create custom tokens (not recommended):
- Must be unique: no two clients same token
- Best format: `alap_token_RANDOM8CHARS`

### Token Security

**If a token leaks:**
1. Go to Admin Panel
2. Find the client in "Access Tokens"
3. Click "Revoke"
4. Old token stops working
5. Generate new token
6. Send to client
7. They login with new token

**Multi-Client Setup (50 clients):**
Each gets their own unique token:
- Client 1: `alap_token_a1b2c3d4`
- Client 2: `alap_token_e5f6g7h8`
- Client 3: `alap_token_i9j0k1l2`
- etc.

---

## 📊 Data Flow Diagram

```
Admin (You)
    ↓
Alap_Admin_Panel.html
    ↓ (add client + generate token)
    ↓
localStorage (your computer)
    ↓ (export customers.json)
    ↓
GitHub repository
    ↓ (auto-webhook)
    ↓
Railway server
    ↓ (reads customers.json)
    ↓
Flask app (app.py)

          Client (Your Customer)
               ↓
          Alap_Client_Panel.html
               ↓ (login with token)
               ↓
          localStorage (their computer)
               ↓ (edit inventory)
               ↓ (upload Excel / text command)
               ↓
          Downloads their inventory.json

               ↓ (share with you)
               ↓
          You import into Admin Panel
               ↓
          Export new customers.json
               ↓
          Push to GitHub → Railway updates
```

---

## 🛠 Troubleshooting

### "Client can't login"
**Problem:** Shows error or blank screen
**Solution:**
1. Verify token is correct (copy from Admin Panel)
2. Verify Business Name matches exactly
3. Refresh browser page
4. Clear browser cache: Settings → Clear browsing data

### "Inventory not showing"
**Problem:** Excel uploaded but products missing
**Solution:**
1. Check Excel format — must have columns:
   - Name (or "Product")
   - Price
   - Size/Details (or "Details")
   - Available (with Yes/No values)
2. No empty rows at top
3. Try uploading again

### "History disappeared"
**Problem:** Change history is gone
**Solution:**
1. Refresh browser
2. Check if localStorage was cleared
3. Recommend client download JSON backup regularly

### "Token generation failed"
**Problem:** Admin Panel not generating tokens
**Solution:**
1. Check browser console (F12)
2. Make sure localStorage not full
3. Try different browser (Chrome, Firefox, Safari)

### "customers.json not updating"
**Problem:** Admin exports but Flask server doesn't read changes
**Solution:**
1. Verify you pushed to GitHub: `git push`
2. Railway webhook received: check Railway logs
3. Check 60-second deploy time
4. Restart Railway server manually

---

## 📝 Excel Template

When clients ask for Excel format:

```
Name | Price | Size/Details | Available
-----|-------|--------------|----------
Sharee | 1200 | Cotton S/M/L | Yes
Salwar | 1500 | Silk M/L/XL | Yes
Panjabi | 900 | Cotton M/L | No
Dupatta | 300 | Pure cotton | Yes
```

Download template format:
```
Column A: Product Name
Column B: Price (number only, e.g., 1200)
Column C: Size/Details (text, e.g., "Cotton S/M/L")
Column D: Available (Yes or No only)
```

---

## 🎯 Workflow For You

### Daily (Ongoing)

**Week 1: Setup**
```
Monday:   Add first client in Admin Panel
Tuesday:  Send them Client Panel HTML + token
Wednesday: Client adds inventory via Excel
Thursday: Admin exports customers.json
Friday:   Push to GitHub, bot goes live
```

**Week 2: Grow**
```
Monday:   Add 2nd client (same process)
Tuesday:  Share Client Panel + token
Wednesday: Export customers.json
Thursday: Push to GitHub
Friday:   Both bots live
```

**Ongoing (Each client adds automatically)**
```
Step 1: Client edits inventory in their panel
Step 2: They tell you to sync (or weekly sync)
Step 3: You download their inventory.json
Step 4: Combine with other clients
Step 5: Push to GitHub
Step 6: Railway updates (60 seconds)
Step 7: Bots use latest inventory
```

---

## 💰 Business Model

### How to Price

**Option 1: Flat Monthly Fee**
- Charge each client: ৳2,000-3,000/month
- Track in Admin Panel

**Option 2: Tiered Pricing**
- Startup: ৳1,500/month (1-100 products)
- Pro: ৳2,500/month (1-500 products)
- Enterprise: ৳5,000/month (unlimited)

**Option 3: Commission Model**
- Charge % of orders bot helps process
- Harder to track with current system
- Need to extend system

### Income Tracking

In Admin Panel:
- Dashboard shows "Monthly Revenue"
- Auto-calculates from all active clients
- Formula: Sum of (Monthly Fee × Active Status)

Example with 5 clients:
```
Client 1: ৳2,000 (active)
Client 2: ৳2,500 (active)
Client 3: ৳0     (paused)
Client 4: ৳1,500 (active)
Client 5: ৳3,000 (active)
---
Total: ৳9,000/month
```

---

## 🔐 Data Privacy

### What Data is Stored?

**In Your Browser (Admin Panel):**
- Client names
- Business info
- Monthly fees
- Access tokens (NOT passwords)

**In Client's Browser (Client Panel):**
- Their inventory
- Their products
- Change history
- ONLY their data (isolated by token)

**On Your Server (Railway):**
- customers.json with all clients' inventory
- Same data as Admin Panel exported

### What is NOT Stored

- Actual customer DMs (those go to Meta, not you)
- Customer personal info
- Payment info (handle separately with Stripe)

### Privacy Policy

For Meta App Review, mention:
```
"Clients can manage their own inventory. 
Data is stored locally in their browser 
and on our secure server. 
We do not share client data with third parties."
```

---

## 📚 Files You Have

1. **Alap_Admin_Panel_v2.html** (NEW)
   - For you (admin)
   - Manage all clients
   - Generate tokens
   - Export data

2. **Alap_Client_Panel.html** (NEW)
   - For your customers
   - Edit inventory
   - Upload Excel
   - View history

3. **Privacy_Policy_Meta_App_Review.docx** (FROM EARLIER)
   - For Meta review
   - Update company name

4. **Alap_Logo_Concepts.svg** (FROM EARLIER)
   - Logo designs for your brand

5. **ALAP_SETUP_GUIDE.md** (REFERENCE)
   - Quick reference guide

---

## 🎓 Next Steps

### This Week
- [ ] Test Admin Panel locally
- [ ] Add a test client
- [ ] Generate test token
- [ ] Test Client Panel with that token
- [ ] Upload test Excel file
- [ ] Add products via text command
- [ ] Verify change history records everything
- [ ] Export customers.json
- [ ] Push to Flask server on Railway

### Next Week
- [ ] Find first real client
- [ ] Add them in Admin Panel
- [ ] Send them Client Panel + token
- [ ] Get their Excel inventory
- [ ] Test bot responds with their products
- [ ] Collect ৳2,000+ payment

### Month 2
- [ ] Add 3-5 more clients
- [ ] Recurring ৳6,000-15,000/month revenue
- [ ] Build self-serve signup page (optional)
- [ ] Add Stripe for auto-payments (optional)
- [ ] Submit Meta App Review if not done

---

## ❓ FAQ

**Q: Can multiple clients use same HTML file?**
A: Yes! Each gets the same Alap_Client_Panel.html. They login with their own token.

**Q: What if a client loses their token?**
A: Go to Admin Panel, find them in "Access Tokens", generate new token.

**Q: Can I edit a client's inventory for them?**
A: Currently no. System is client-managed. You can add this feature later.

**Q: What if client's inventory has 500 products?**
A: System works fine. Panel shows all products with search. Handles large files.

**Q: Do I have to push to GitHub every time client updates?**
A: Not real-time, but this is the simple workflow. Later you can:
- Auto-sync using webhooks
- Use a database instead of JSON
- Create API endpoint for live updates

**Q: What if I have 100 clients?**
A: System still works but localStorage has limits (~5MB). Move to database:
- Firebase Firestore
- MongoDB
- PostgreSQL
- AWS DynamoDB

**Q: Can clients see other clients' inventory?**
A: No. Each token shows only that client's data.

**Q: Is this secure?**
A: For MVP yes. For production (100+ clients):
- Move to server-side database
- Add user authentication (not just tokens)
- Use HTTPS
- Add rate limiting
- Encrypt sensitive data

---

## 🎉 You're Done!

You now have a **complete two-sided platform**:

✅ Admin Panel to manage clients  
✅ Client Panel for customers  
✅ Inventory management  
✅ Change history/audit log  
✅ Excel import  
✅ Text commands  
✅ Token-based access  
✅ Data export  
✅ Multi-client support  

**Next action:** Open Admin Panel, add your first test client, and try it out!

Questions? Check the setup guide or refer to the inline help in each panel.

Good luck! 🚀
