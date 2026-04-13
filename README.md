# OutreachBot

A simple, self-hosted email outreach tool for reaching out to businesses that don't have websites. Add contacts (e.g. businesses you find on Google Maps without a site), customize email templates, and send personalized outreach emails — all from a clean dashboard.

## Features

- **Quick-send dashboard** — add a business + email and fire off a personalized outreach email in one click
- **Contact management** — add, edit, bulk-import, filter, and track status (pending / sent / replied / converted)
- **Smart email templates** — Jinja2-powered templates with variables like `{{ business_name }}`, `{{ city }}`, `{{ industry }}`, `{{ sender_name }}`, etc.
- **Email preview** — see exactly what your email will look like before sending
- **Batch sending** — send to all pending contacts at once
- **Activity log** — track every email sent, with error details for failures
- **SMTP settings** — configure any SMTP provider (Gmail, Outlook, custom) right from the UI
- **Bulk import** — paste JSON or CSV to import many contacts at once

## Quick Start

```bash
# 1. Clone and enter the repo
git clone <your-repo-url> && cd outreach-bot

# 2. Create a virtual environment
python3 -m venv venv && source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Copy and fill in .env
cp .env.example .env
# Edit .env with your SMTP credentials, or configure them in the Settings UI

# 5. Run the app
python app.py
```

Open **http://localhost:5000** in your browser.

## Configuration

You can configure everything from the **Settings** page in the dashboard, or via environment variables in `.env`:

| Variable | Description |
|---|---|
| `SMTP_SERVER` | SMTP host (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |
| `SMTP_USERNAME` | Your email login |
| `SMTP_PASSWORD` | Your email password or app password |
| `SENDER_NAME` | Your name (used in email signature) |
| `SENDER_EMAIL` | Your "from" email address |
| `SENDER_PHONE` | Your phone number (optional, shown in emails) |
| `SENDER_WEBSITE` | Your website URL (optional, shown in emails) |

### Gmail Setup

1. Enable 2-factor authentication on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use that password as `SMTP_PASSWORD`

## Template Variables

Use these in your email templates (subject and body):

| Variable | Description |
|---|---|
| `{{ business_name }}` | The business you're contacting |
| `{{ contact_name }}` | Contact person's name |
| `{{ email }}` | Their email address |
| `{{ industry }}` | Business industry/category |
| `{{ city }}` | Business location |
| `{{ notes }}` | Your notes about the business |
| `{{ sender_name }}` | Your name |
| `{{ sender_email }}` | Your email |
| `{{ sender_phone }}` | Your phone number |
| `{{ sender_website }}` | Your website URL |

## Project Structure

```
├── app.py                 # Flask app: models, API routes, email engine
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── templates/
│   ├── base.html          # Shared layout with sidebar navigation
│   ├── dashboard.html     # Main dashboard with quick-send form
│   ├── contacts.html      # Contact list management
│   ├── templates.html     # Email template editor
│   └── settings.html      # SMTP and sender configuration
└── static/
    ├── css/style.css      # Dashboard styles
    └── js/app.js          # Shared JS utilities
```

## License

MIT
