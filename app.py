import os
import sqlite3
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, g
)
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key-change-me")

DATABASE = os.path.join(app.instance_path, "outreach.db")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        os.makedirs(app.instance_path, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            business_name TEXT NOT NULL,
            contact_name TEXT,
            email TEXT NOT NULL,
            industry TEXT,
            custom_detail TEXT,
            subject TEXT,
            body TEXT,
            status TEXT DEFAULT 'draft',
            error_message TEXT,
            created_at TEXT,
            sent_at TEXT
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    defaults = {
        "smtp_host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": os.getenv("SMTP_PORT", "587"),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "from_email": os.getenv("FROM_EMAIL", ""),
        "from_name": os.getenv("FROM_NAME", ""),
    }
    for k, v in defaults.items():
        db.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            (k, v),
        )
    db.commit()


with app.app_context():
    init_db()


def get_setting(key):
    row = get_db().execute(
        "SELECT value FROM settings WHERE key = ?", (key,)
    ).fetchone()
    return row["value"] if row else ""


def set_setting(key, value):
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
        (key, value),
    )
    db.commit()


# ---------------------------------------------------------------------------
# Email generation – builds a natural, soft-pitch outreach email
# ---------------------------------------------------------------------------

TEMPLATES = {
    "default": {
        "subject": "Quick thought about {business_name}'s online presence",
        "body": """Hi{contact_greeting},

I came across {business_name} while browsing {industry_context}and noticed you don't seem to have a website set up yet. It caught my attention because a lot of customers today search online before visiting a business — and right now, those potential customers might not be finding you.

A clean, professional website can make a real difference:

• It gives customers a place to learn about what you offer — anytime, day or night.
• It builds trust and credibility before someone even walks through your door.
• It helps you show up in Google searches when people look for {industry_search}in your area.
• It's a simple way to share your hours, location, contact info, and what makes {business_name} stand out.

{custom_paragraph}I help small businesses get online with a personalized website — nothing cookie-cutter. I handle the whole process: design, setup, and launch, tailored to your business so it actually represents who you are.

If that sounds like something you'd be interested in exploring, I'd love to chat — no pressure at all. Even a quick call to see if it'd be a good fit would be great.

Either way, wishing you all the best with {business_name}!

Best,
{from_name}""",
    },
    "google_profile": {
        "subject": "Noticed {business_name} on Google — quick idea",
        "body": """Hi{contact_greeting},

I found {business_name} through your Google Business profile{industry_context_alt}. Your listing looks solid, but I noticed there's no website linked — which means people who want to learn more about you don't really have anywhere to go after finding you on Google.

Here's why that matters more than you might think:

• Google actually ranks businesses with websites higher in local search results.
• A website lets you tell your story — not just show a pin on a map.
• Customers can check out your services, read reviews, and contact you all in one place.
• It works 24/7, even when you're closed.

{custom_paragraph}I specialize in building clean, professional websites for businesses like yours. I take care of everything — design, content, setup, and launch — so you don't have to worry about the technical side.

If you've ever thought about getting a site up, I'd be happy to walk you through what it could look like for {business_name}. No hard sell — just a conversation to see if it makes sense for you.

Hope to hear from you!

{from_name}""",
    },
}


def generate_email(data: dict, template_key: str = "default") -> dict:
    template = TEMPLATES.get(template_key, TEMPLATES["default"])

    contact_greeting = ""
    if data.get("contact_name"):
        contact_greeting = f" {data['contact_name']}"

    industry_context = ""
    industry_context_alt = ""
    industry_search = "businesses"
    if data.get("industry"):
        industry_context = f"in the {data['industry']} space "
        industry_context_alt = f" and it's clear you're doing great work in the {data['industry']} space"
        industry_search = data["industry"]

    custom_paragraph = ""
    if data.get("custom_detail"):
        custom_paragraph = f"{data['custom_detail']}\n\n"

    from_name = get_setting("from_name") or "Your Name"

    subject = template["subject"].format(
        business_name=data["business_name"],
    )
    body = template["body"].format(
        business_name=data["business_name"],
        contact_greeting=contact_greeting,
        industry_context=industry_context,
        industry_context_alt=industry_context_alt,
        industry_search=industry_search,
        custom_paragraph=custom_paragraph,
        from_name=from_name,
    )

    return {"subject": subject, "body": body}


# ---------------------------------------------------------------------------
# SMTP sending
# ---------------------------------------------------------------------------

def send_email(to_email: str, subject: str, body: str):
    host = get_setting("smtp_host")
    port = int(get_setting("smtp_port") or 587)
    username = get_setting("smtp_username")
    password = get_setting("smtp_password")
    from_email = get_setting("from_email")
    from_name = get_setting("from_name")

    if not all([host, username, password, from_email]):
        raise ValueError("SMTP settings are not fully configured. Go to Settings to set them up.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>" if from_name else from_email
    msg["To"] = to_email

    plain_part = MIMEText(body, "plain")
    msg.attach(plain_part)

    html_body = body.replace("\n", "<br>")
    html_body = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                font-size: 15px; line-height: 1.6; color: #333; max-width: 600px;">
        {html_body}
    </div>"""
    html_part = MIMEText(html_body, "html")
    msg.attach(html_part)

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(username, password)
        server.sendmail(from_email, to_email, msg.as_string())


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    db = get_db()
    total = db.execute("SELECT COUNT(*) as c FROM emails").fetchone()["c"]
    sent = db.execute("SELECT COUNT(*) as c FROM emails WHERE status='sent'").fetchone()["c"]
    failed = db.execute("SELECT COUNT(*) as c FROM emails WHERE status='failed'").fetchone()["c"]
    drafts = db.execute("SELECT COUNT(*) as c FROM emails WHERE status='draft'").fetchone()["c"]
    recent = db.execute(
        "SELECT * FROM emails ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    return render_template(
        "dashboard.html",
        stats={"total": total, "sent": sent, "failed": failed, "drafts": drafts},
        recent=recent,
    )


@app.route("/compose", methods=["GET", "POST"])
def compose():
    if request.method == "POST":
        data = {
            "business_name": request.form.get("business_name", "").strip(),
            "contact_name": request.form.get("contact_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "industry": request.form.get("industry", "").strip(),
            "custom_detail": request.form.get("custom_detail", "").strip(),
        }

        if not data["business_name"] or not data["email"]:
            flash("Business name and email are required.", "error")
            return render_template("compose.html", form=data)

        template_key = request.form.get("template", "default")
        email_content = generate_email(data, template_key)

        email_id = str(uuid.uuid4())
        db = get_db()
        db.execute(
            """INSERT INTO emails
               (id, business_name, contact_name, email, industry,
                custom_detail, subject, body, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?)""",
            (
                email_id,
                data["business_name"],
                data["contact_name"],
                data["email"],
                data["industry"],
                data["custom_detail"],
                email_content["subject"],
                email_content["body"],
                datetime.utcnow().isoformat(),
            ),
        )
        db.commit()

        return redirect(url_for("preview", email_id=email_id))

    return render_template("compose.html", form={})


@app.route("/preview/<email_id>")
def preview(email_id):
    db = get_db()
    email = db.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    if not email:
        flash("Email not found.", "error")
        return redirect(url_for("dashboard"))
    return render_template("preview.html", email=email)


@app.route("/edit/<email_id>", methods=["GET", "POST"])
def edit_email(email_id):
    db = get_db()
    email = db.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    if not email:
        flash("Email not found.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()
        db.execute(
            "UPDATE emails SET subject = ?, body = ? WHERE id = ?",
            (subject, body, email_id),
        )
        db.commit()
        flash("Email updated.", "success")
        return redirect(url_for("preview", email_id=email_id))

    return render_template("edit.html", email=email)


@app.route("/send/<email_id>", methods=["POST"])
def send(email_id):
    db = get_db()
    email = db.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
    if not email:
        flash("Email not found.", "error")
        return redirect(url_for("dashboard"))

    try:
        send_email(email["email"], email["subject"], email["body"])
        db.execute(
            "UPDATE emails SET status = 'sent', sent_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), email_id),
        )
        db.commit()
        flash(f"Email sent to {email['email']}!", "success")
    except Exception as e:
        db.execute(
            "UPDATE emails SET status = 'failed', error_message = ? WHERE id = ?",
            (str(e), email_id),
        )
        db.commit()
        flash(f"Failed to send: {e}", "error")

    return redirect(url_for("preview", email_id=email_id))


@app.route("/delete/<email_id>", methods=["POST"])
def delete_email(email_id):
    db = get_db()
    db.execute("DELETE FROM emails WHERE id = ?", (email_id,))
    db.commit()
    flash("Email deleted.", "success")
    return redirect(url_for("history"))


@app.route("/history")
def history():
    db = get_db()
    status_filter = request.args.get("status", "all")
    if status_filter != "all":
        emails = db.execute(
            "SELECT * FROM emails WHERE status = ? ORDER BY created_at DESC",
            (status_filter,),
        ).fetchall()
    else:
        emails = db.execute(
            "SELECT * FROM emails ORDER BY created_at DESC"
        ).fetchall()
    return render_template("history.html", emails=emails, status_filter=status_filter)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        keys = ["smtp_host", "smtp_port", "smtp_username", "smtp_password",
                "from_email", "from_name"]
        for k in keys:
            val = request.form.get(k, "").strip()
            if k == "smtp_password" and val == "":
                continue
            set_setting(k, val)
        flash("Settings saved.", "success")
        return redirect(url_for("settings"))

    current = {}
    for k in ["smtp_host", "smtp_port", "smtp_username", "smtp_password",
              "from_email", "from_name"]:
        current[k] = get_setting(k)
    return render_template("settings.html", settings=current)


@app.route("/test-smtp", methods=["POST"])
def test_smtp():
    try:
        host = get_setting("smtp_host")
        port = int(get_setting("smtp_port") or 587)
        username = get_setting("smtp_username")
        password = get_setting("smtp_password")

        if not all([host, username, password]):
            return jsonify({"ok": False, "message": "SMTP settings incomplete."})

        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(username, password)

        return jsonify({"ok": True, "message": "Connection successful!"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
