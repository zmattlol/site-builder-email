# Site Builder Outreach Dashboard

A lightweight email outreach dashboard for offering personalized business websites.

## What this does

- Lets you enter business + offer details in a simple form.
- Generates a friendly outreach email with a subtle benefits pitch.
- Allows editing before sending.
- Sends via SMTP (or test mode for safe previews).
- Stores outreach history in a local JSON file.

## Quick start

1. Install dependencies:

```bash
npm install
```

2. Copy and configure environment variables:

```bash
cp .env.example .env
```

3. Start the app:

```bash
npm start
```

4. Open:

```text
http://localhost:3000
```

## Environment variables

See `.env.example`:

- `PORT` - app port (default: `3000`)
- `SMTP_HOST` - SMTP server host
- `SMTP_PORT` - SMTP server port
- `SMTP_USER` - SMTP username
- `SMTP_PASS` - SMTP password/app-password
- `SMTP_FROM_EMAIL` - from email address
- `SMTP_FROM_NAME` - display name
- `TEST_MODE` - `true` disables actual sending and logs emails only

## How to use

1. Fill out business details and your offer.
2. Leave "Send email now" unchecked to generate a preview safely.
3. Review and tweak your inputs.
4. Check "Send email now" and submit to send (or simulate if `TEST_MODE=true`).
5. Review deliveries and failures in Recent Activity.

## Notes

- This tool is designed for legitimate, consent-aware business outreach.
- Add your own qualification process and suppression list before production campaigns.
