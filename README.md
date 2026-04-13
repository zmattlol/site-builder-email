# Site Builder Email Outreach Bot

A simple, self-hosted dashboard for sending personalized outreach emails to businesses that don't have a website. Plug in a few business details and an email address, and the bot generates a natural, soft-pitch email offering your web design services.

## What It Does

- **Compose**: Enter a business name, contact person, industry, and email — the bot generates a personalized outreach email.
- **Templates**: Two built-in templates — one for businesses with no online presence, one for businesses that have a Google profile but no website.
- **Preview & Edit**: Review the generated email, tweak the copy if you want, then send.
- **Send**: Emails are sent via SMTP (works with Gmail, Outlook, or any provider).
- **Dashboard**: See stats (total, sent, drafts, failed) and recent outreach at a glance.
- **History**: Filter and browse all past emails by status.
- **Settings**: Configure SMTP credentials and your sender name from the UI.

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url> && cd site-builder-email

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your environment
cp .env.example .env
# Edit .env with your SMTP credentials (or configure in the Settings page)

# 4. Run the app
python app.py
```

Then open **http://localhost:5000** in your browser.

## SMTP Setup (Gmail)

1. Enable 2-Step Verification on your Google account.
2. Go to **App Passwords** (search for it in your Google account security settings).
3. Generate a password for "Mail".
4. Use that 16-character password as your SMTP password.

| Setting       | Value              |
| ------------- | ------------------ |
| SMTP Host     | `smtp.gmail.com`   |
| SMTP Port     | `587`              |
| Username      | your Gmail address |
| Password      | app password       |

You can also configure these from the **Settings** page in the dashboard.

## Project Structure

```
app.py              # Flask application (routes, email generation, SMTP)
requirements.txt    # Python dependencies
.env.example        # Example environment variables
templates/
  base.html         # Layout with sidebar navigation
  dashboard.html    # Stats overview + recent emails
  compose.html      # New outreach form
  preview.html      # Email preview before sending
  edit.html         # Edit subject/body
  history.html      # All emails with status filters
  settings.html     # SMTP configuration UI
```

## Email Templates

**General (no website found):** A friendly email noting you couldn't find their website, highlighting benefits of having one (24/7 availability, Google visibility, credibility), and softly offering your services.

**Google Profile (has listing, no site):** Tailored for businesses found via Google Business — acknowledges their profile, explains why linking a website boosts their ranking, and offers to help.

Both templates support:
- Personalized greeting (contact name)
- Industry-specific language
- Custom detail insertion (your own personal touch)
- Your name in the sign-off

## License

MIT
