# site-builder-email

A lightweight outreach dashboard for website-offer emails.

This project gives you a simple local dashboard where you can:

- add business leads manually
- save notes about what you noticed online
- generate a personalized email draft offering to build them a custom website
- edit the draft before sending
- send the reviewed email through your own SMTP inbox
- mark leads as do not contact

## Why this app is structured this way

The app is built for one-to-one reviewed outreach, not bulk email blasting. You enter each lead yourself, review the copy, and send it intentionally from your own email account.

## Stack

- Python 3 standard library only
- SQLite for local storage
- Plain HTML, CSS, and JavaScript for the dashboard

## Run locally

1. Make sure you have Python 3.11+ installed.
2. Set your SMTP environment variables:

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="you@example.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_FROM_EMAIL="you@example.com"
export SMTP_FROM_NAME="Your Name"
```

3. Start the app:

```bash
python3 app.py
```

4. Open:

```text
http://127.0.0.1:8000
```

## Optional environment variables

- `HOST` - defaults to `127.0.0.1`
- `PORT` - defaults to `8000`
- `OUTREACH_DB_PATH` - defaults to `./data/outreach.db`
- `SMTP_USE_STARTTLS` - defaults to `true`

## Workflow

1. Add a business lead with the business name and email.
2. Fill in any useful details like location, business type, Google profile URL, offer summary, and notes.
3. Click **Generate draft**.
4. Review or edit the subject and body.
5. Click **Send email** when ready.

## Tests

Run:

```bash
python3 -m unittest discover -s tests
```

