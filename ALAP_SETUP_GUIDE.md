# Alap — Two-Sided System Setup Guide

You now have **3 main components**:

1. **Admin Panel** (for you) — Manage all clients
2. **Client Panel** (for your customers) — Edit their own inventory
3. **Flask Server** (on Railway) — The actual bot

---

## Quick Start

### Step 1: Admin Panel
Open `Alap_Admin_Panel.html` in your browser
- Add clients (business name, page ID, token)
- Download `customers.json`
- Push to GitHub → Railway deploys

### Step 2: Client Panel
Each client gets their own login link to `Alap_Client_Panel.html`
- Login with: Business Name + Access Token (generated in admin)
- Upload Excel file with inventory
- Edit products manually
- View change history
- Download JSON anytime

### Step 3: Flask Server
Your app.py reads `customers.json`
- One entry per client
- Bot replies using that client's inventory + Q&A

---

## How It Works (End-to-End)

```
You (Admin)                  Client                     Facebook Customer
    ↓                            ↓                             ↓
Admin Panel                 Client Panel               Sends DM to Page
  ↓ add client                  ↓                             ↓
  ↓ download JSON          Login with token              Server gets DM
  ↓ push to GitHub              ↓                             ↓
  ↓                        Edit inventory              AI reads inventory
  ↓                             ↓                             ↓
  ↓                        Change history              Generates reply
  ↓                             ↓                             ↓
Railway deploys                 ↓                       Sends reply back
  ↓                        Download JSON               Customer sees it
  ↓                             ↓
Bot is live              (backup if needed)
```

---

## Client Workflow

### 1. First Time Setup
1. You give client: `Alap_Client_Panel.html` link + their token
2. Client opens the file in browser
3. Client enters: Business Name + Token
4. Client is logged in

### 2. Edit Inventory
**Option A — Upload Excel**
- Client downloads Excel template
- Fills it in: Product | Price | Size | Available
- Uploads to Client Panel
- History auto-recorded

**Option B — Type Commands**
- Client types: `Sharee 1200 Cotton M/L Yes`
- Panel auto-adds product
- History auto-recorded

**Option C — Manual Edit**
- Click Edit button on any product
- Change details
- History auto-recorded

### 3. View Changes
- Switch to "Change History" tab
- See everything they changed
- Timestamp for each change
- Type of change (Add/Edit/Delete/Import)

### 4. Download Backup
- "Download JSON" button
- Gets their current inventory as JSON file
- Can save locally

---

## Token System

### What's a Token?
A unique code that gives a client access to **only their own** inventory.

### How to Generate Tokens

**In Admin Panel:**
1. Go to "Settings" tab
2. Click "Generate Client Token"
3. A random code appears (e.g., `alap_token_x7k9p2m1`)
4. Copy it → Send to client
5. Client uses it to login

### Token Safety
- Each client has their own unique token
- One token = one client account
- If a token leaks, regenerate it in Admin Panel
- Change password-style

---

## Admin Panel Features

### Manage Clients
```
Admin Panel
├── Dashboard
│   ├── Total clients count
│   ├── Active vs Paused
│   ├── Monthly revenue
│   └── Recent activity
├── Clients List
│   ├── See all clients
│   ├── Edit client info
│   └── Delete client
├── Generate Tokens
│   ├── Create new token
│   ├── Manage existing tokens
│   └── Revoke access
├── Client Settings
│   ├── Set monthly fee
│   ├── Pause/resume bot
│   └── View client stats
└── Download customers.json
    └── Push to GitHub
```

---

## File Structure

```
Your Project Folder
├── app.py (Flask server)
├── customers.json (auto-generated)
├── requirements.txt
├── .git/
└── Admin files
    ├── Alap_Admin_Panel.html (for you)
    └── Alap_Client_Panel.html (for clients)
```

---

## Deployment Checklist

- [ ] Privacy Policy created and hosted
- [ ] Admin Panel tested locally
- [ ] Client Panel tested with a test client
- [ ] Flask server updated to read multiple clients
- [ ] customers.json format correct
- [ ] Token system working
- [ ] Excel import tested
- [ ] Text command parser working
- [ ] History tracking recording changes
- [ ] GitHub webhook subscribed for all client pages
- [ ] Railway deployment successful
- [ ] Bot responds to test DMs

---

## Troubleshooting

**Client can't login?**
- Verify token is correct
- Token is case-sensitive
- Make sure client can access the HTML file

**History not showing?**
- Refresh browser
- Check browser console for errors
- Clear localStorage if corrupted

**Excel import not working?**
- Check file format (.xlsx or .csv)
- Column names must match: Name, Price, Size/Details, Available
- No empty rows at top

**Bot doesn't reply?**
- Check customers.json is valid JSON
- Verify page ID is correct
- Check Flask server logs on Railway
- Confirm permanent token never expires

---

## Next Steps (Advanced)

1. **Database instead of localStorage**
   - Move clients.json to a database
   - Better for 50+ clients

2. **Self-serve signup**
   - Client visits signup page
   - Creates own account
   - Automatically gets token

3. **Stripe payments**
   - Auto-charge monthly
   - Stop bot if payment fails
   - Usage tracking per client

4. **Email notifications**
   - Send customer order confirmations
   - Weekly inventory low-stock alerts
   - Integration with Gmail

5. **Multi-language support**
   - Extend to all major languages
   - Clients choose in settings

---

## Questions?

- Admin Panel help: Check "Deploy" tab inside
- Client Panel help: Built-in tooltips
- Token issues: Regenerate in Admin Settings
- Inventory format: Check Excel template download
