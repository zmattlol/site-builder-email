# OutreachBot — Business Website Outreach Dashboard

A self-hosted Flask web app that helps you email local businesses (found via Google Maps / Yelp) that don't have a website yet, pitching your web design services.

---

## Features

| Feature | Description |
|---|---|
| **Lead management** | Add businesses with name, contact, email, industry, location, and notes |
| **Live email preview** | See the personalized email render in real-time as you type |
| **Industry-aware emails** | Tailored benefit snippets per industry (restaurant, plumber, salon, etc.) |
| **One-click send** | Send to a single lead or bulk-send all pending leads |
| **Campaign grouping** | Organize leads into named campaigns (e.g. "Chicago Restaurants June") |
| **Email log** | Full history of every email sent, with status and error tracking |
| **Settings panel** | Configure SMTP, your name/title/phone, and a custom service description |

---

## Quick Start

### 1. Clone & install

```bash
cd outreach_bot
pip install -r requirements.txt
```

### 2. Run the app

```bash
python3 run.py
```

Open **http://localhost:5000** in your browser.

### 3. Configure Settings first

Go to **Settings** and fill in:

- **SMTP Host / Port / User / Password** — your outgoing mail server  
  - Gmail: host `smtp.gmail.com`, port `587`, use an [App Password](https://myaccount.google.com/apppasswords)
- **Your Name, Title, Phone, Website** — appears in every email signature
- **Service Description** — optional custom paragraph about what you offer

### 4. Add Leads

Go to **Add Lead** and fill in:

- Business name (required)
- Their email (required)
- Contact name (optional — personalizes the greeting)
- Industry — selects the right benefit snippet automatically
- Location — appears naturally in the email copy
- Personal note — shows as a P.S. at the bottom

Watch the **Live Preview** panel on the right update as you type.

### 5. Send

- Click **Send Email** from any lead's detail page to send one at a time
- Use **Bulk Send** on the dashboard to fire all pending leads at once (1.5s delay between sends)

---

## Email Template

Each email is personalized and includes:

1. **Warm, low-pressure opener** — "I came across [Business] and wanted to reach out personally"
2. **Industry-specific insight** — e.g. for a plumber: *"When a pipe bursts at midnight, people Google for help immediately"*
3. **What you offer** — your configured service blurb or a polished default
4. **Bullet-point value list** — services, hours, Google-friendly setup, mobile-optimized
5. **Soft CTA** — "If this sounds interesting, feel free to reply…"
6. **Personal note P.S.** — if you added one for that lead
7. **Unsubscribe footer** — professional opt-out language

---

## Project Structure

```
outreach_bot/
├── app.py              # Flask app, routes, DB logic, email sending
├── email_service.py    # Email template generation, subject lines, industry snippets
├── run.py              # Entry point
├── requirements.txt
├── outreach.db         # SQLite database (auto-created on first run)
└── templates/
    ├── base.html       # Sidebar layout, nav, flash messages
    ├── dashboard.html  # Stats, bulk send, recent leads
    ├── leads.html      # Filterable leads table
    ├── new_lead.html   # Add lead form + live email preview
    ├── lead_detail.html# Lead info, send button, email preview, send history
    ├── settings.html   # SMTP + identity + service blurb config
    └── log.html        # Full email send history
```

---

## Gmail Setup (Recommended)

1. Enable 2-Step Verification on your Google account
2. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
3. Create an App Password for "Mail"
4. In OutreachBot Settings:
   - SMTP Host: `smtp.gmail.com`
   - SMTP Port: `587`
   - SMTP Username: your Gmail address
   - SMTP Password: the 16-character App Password

---

## Environment Variable

For production, set a real secret key:

```bash
export SECRET_KEY="your-random-secret"
python3 run.py
```
