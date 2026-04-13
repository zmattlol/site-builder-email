# Site Builder Outreach Dashboard

A lightweight Next.js dashboard for reaching out to local businesses that do not have
their own website yet.

The app lets you:

- define your website offer once
- plug in a business name, email, and a few personalization details
- preview a soft-sell outreach email before sending
- save drafts and keep a simple outreach history
- send messages through your own SMTP provider

## What it does

This project is built around the workflow you described:

1. Add your offer details
2. Add a prospect's business name and email
3. Optionally add context like their city, Google profile, or why a website would help
4. Review the generated email
5. Save the draft or send it from the dashboard

The email template is designed to:

- mention that the business appears to rely on a Google Business Profile or similar listing
- explain the benefits of having a personalized website in a subtle way
- ease into a soft CTA instead of sounding pushy

## Tech stack

- Next.js App Router
- React
- TypeScript
- Nodemailer
- File-based storage (`data/prospects.json`)

## Getting started

Install dependencies:

```bash
npm install
```

Copy the example env file and fill in your SMTP credentials:

```bash
cp .env.example .env.local
```

Required values:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_SECURE`
- `SMTP_FROM` or `SMTP_USER`

Then run the app:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Environment variables

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-smtp-user
SMTP_PASS=your-smtp-password
SMTP_FROM=your-name@example.com
SMTP_REPLY_TO=reply@example.com
```

## How data is stored

Saved prospects are written to:

```text
data/prospects.json
```

That keeps the first version simple and easy to run locally. If you want to deploy this
for production use later, you would probably swap the JSON file for a database.

## Notes

- The send button stays disabled until SMTP is configured.
- The preview always works, even without SMTP.
- The dashboard includes a simple opt-out line field you can keep or change.
- Use the tool responsibly and make sure your outreach complies with local email and
  anti-spam rules.
