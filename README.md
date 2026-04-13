# Website Outreach Dashboard

A simple outreach bot + dashboard for pitching website services to local businesses.

You can:

- Add business leads (name, contact, email, city, notes, Google profile link)
- Save your SMTP settings (Gmail, Mailgun, SendGrid SMTP, etc.)
- Customize a reusable outreach script with placeholders
- Preview each email before sending
- Send one-by-one or in bulk
- Track send attempts and lead status

---

## Features

### Lead manager
- Store leads in SQLite
- Keep lead statuses (`new`, `contacted`, `replied`, `uninterested`)
- Save notes for personalization

### Outreach message builder
- Subject and body templates with placeholders:
  - `{{business_name}}`
  - `{{contact_name}}`
  - `{{contact_name_or_business}}`
  - `{{city}}`
  - `{{city_suffix}}`
  - `{{notes}}`
  - `{{google_profile_url}}`
  - `{{offer}}`
  - `{{benefits}}`
  - `{{cta}}`
  - `{{sender_name}}`

### Email sending
- SMTP sending with optional STARTTLS
- Supports custom `From` and `Reply-To`
- Logs success/failure per lead

### Dashboard UX
- Single page for adding leads + editing templates + campaign sending
- “Send selected” bulk action
- Email preview screen

---

## Quick start

### 1) Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Create env file

```bash
cp .env.example .env
```

Optional values to edit in `.env`:

- `FLASK_SECRET_KEY` (recommended for sessions/flash messages)
- `OUTREACH_DB_PATH` (default: `outreach.db`)

### 4) Run app

```bash
python app.py
```

Open:

`http://127.0.0.1:5000`

---

## SMTP notes

You must use a valid SMTP provider and credentials.

Common examples:
- Gmail with app password
- Mailgun SMTP credentials
- SendGrid SMTP credentials
- Any business mail server with SMTP enabled

If emails fail, check:
- host/port
- TLS toggle
- username/password
- provider sending limits

---

## Responsible outreach guidance

This app helps with cold outreach, so you should follow local regulations and platform terms:

- Send only relevant business-to-business outreach
- Include truthful identity and intent
- Respect opt-outs / do-not-contact requests
- Keep volume gradual to protect deliverability
- Avoid misleading claims

---

## Stack

- Flask
- SQLite
- Vanilla HTML/CSS + a tiny bit of JS
