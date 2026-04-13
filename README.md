# site-builder-email

Simple outreach dashboard to help you:

- Enter business + contact details
- Generate a personalized outreach email
- Send it directly with your SMTP account

## What this app does

This tool is focused on your use case:

- You find a local business profile that has no website
- You plug in a few details (business name, city, service type, etc.)
- The app drafts an email that:
  - politely introduces your website setup offer
  - highlights website benefits in a subtle way
  - ends with a light "if you're interested" call-to-action
- You can edit the draft and send it from the dashboard

## Quick start

1. Install dependencies:

```bash
npm install
```

2. Create your env file:

```bash
cp .env.example .env
```

3. Fill in `.env` with your SMTP credentials.

4. Run the app:

```bash
npm start
```

5. Open:

```text
http://localhost:3000
```

## Environment variables

Required for sending:

- `SMTP_HOST`
- `SMTP_PORT` (usually `587`)
- `SMTP_SECURE` (`false` for 587, `true` for 465)
- `SMTP_USER`
- `SMTP_PASS`
- `SMTP_FROM` (e.g. `Your Name <you@domain.com>`)

Optional default values shown in the dashboard:

- `DEFAULT_SENDER_NAME`
- `DEFAULT_SENDER_COMPANY`
- `DEFAULT_OFFER_SUMMARY`
- `DEFAULT_CTA_LINE`

## API endpoints

- `GET /api/health` - health check
- `GET /api/config` - returns default sender/offer config from env
- `POST /api/generate-email` - generates subject/body draft
- `POST /api/send-email` - sends email using SMTP

## Responsible outreach notes

When sending outreach emails, always follow local anti-spam and privacy laws. Use relevant targeting, honest messaging, and stop contacting recipients who opt out.
