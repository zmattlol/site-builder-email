# site-builder-email

A simple outreach dashboard for sending personalized "you should have a website"
emails to businesses that do not yet have a dedicated site.

## What it does

- Lets you enter a business name, email, location, and a few offer details
- Generates a softer outreach email that introduces the value of a website
- Sends the email through your SMTP provider
- Stores sent outreach history locally in `data/leads.json`
- Gives you a live preview in a simple browser dashboard

## Tech stack

- Node.js
- Express
- EJS
- Nodemailer

## Setup

1. Install dependencies:

   ```bash
   npm install
   ```

2. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

3. Add your SMTP details in `.env`.

   Example:

   ```env
   PORT=3000
   SMTP_HOST=smtp.example.com
   SMTP_PORT=587
   SMTP_SECURE=false
   SMTP_USER=your-smtp-username
   SMTP_PASS=your-smtp-password
   SMTP_FROM="Your Name <you@example.com>"

   DEFAULT_SENDER_NAME=Your Name
   DEFAULT_SENDER_EMAIL=you@example.com
   DEFAULT_SENDER_PHONE=
   DEFAULT_SENDER_WEBSITE=
   ```

4. Start the dashboard:

   ```bash
   npm start
   ```

5. Open:

   ```text
   http://localhost:3000
   ```

## How to use it

1. Paste in the recipient email and business details
2. Adjust the offer and benefits to match your service
3. Check the live email preview
4. Send the outreach email from the dashboard
5. Review the sent history table at the bottom of the page

## Notes

- The app does not scrape Google Business Profiles for you. It assumes you are
  pasting in the business details and email yourself.
- The actual sender is your configured SMTP account. The signature inside the
  email body comes from the sender fields in the dashboard.
- A focused unit test for the email template is included and can be run with:

  ```bash
  npm test
  ```
