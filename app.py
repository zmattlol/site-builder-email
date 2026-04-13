import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from jinja2 import Template

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///outreach.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(200), default="")
    email = db.Column(db.String(200), nullable=False)
    industry = db.Column(db.String(200), default="")
    city = db.Column(db.String(200), default="")
    notes = db.Column(db.Text, default="")
    status = db.Column(db.String(50), default="pending")  # pending, sent, replied, converted
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    sent_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "business_name": self.business_name,
            "contact_name": self.contact_name,
            "email": self.email,
            "industry": self.industry,
            "city": self.city,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


class EmailTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "subject": self.subject,
            "body": self.body,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smtp_server = db.Column(db.String(200), default="smtp.gmail.com")
    smtp_port = db.Column(db.Integer, default=587)
    smtp_username = db.Column(db.String(200), default="")
    smtp_password = db.Column(db.String(200), default="")
    sender_name = db.Column(db.String(200), default="")
    sender_email = db.Column(db.String(200), default="")
    sender_phone = db.Column(db.String(50), default="")
    sender_website = db.Column(db.String(300), default="")

    def to_dict(self):
        return {
            "id": self.id,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "smtp_username": self.smtp_username,
            "sender_name": self.sender_name,
            "sender_email": self.sender_email,
            "sender_phone": self.sender_phone,
            "sender_website": self.sender_website,
        }


class EmailLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("contact.id"), nullable=False)
    subject = db.Column(db.String(500))
    status = db.Column(db.String(50), default="sent")  # sent, failed
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    contact = db.relationship("Contact", backref=db.backref("email_logs", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "contact_id": self.contact_id,
            "business_name": self.contact.business_name if self.contact else "",
            "subject": self.subject,
            "status": self.status,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
        }


# ---------------------------------------------------------------------------
# Database init & seed
# ---------------------------------------------------------------------------

def seed_defaults():
    """Create default settings and email templates if they don't exist."""
    if not Settings.query.first():
        settings = Settings(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            sender_name=os.getenv("SENDER_NAME", ""),
            sender_email=os.getenv("SENDER_EMAIL", ""),
            sender_phone=os.getenv("SENDER_PHONE", ""),
            sender_website=os.getenv("SENDER_WEBSITE", ""),
        )
        db.session.add(settings)

    if not EmailTemplate.query.first():
        default_template = EmailTemplate(
            name="Friendly Website Inquiry",
            subject="Quick question about {{ business_name }}'s online presence",
            body="""Hi{{ ' ' + contact_name if contact_name else '' }},

I came across {{ business_name }}{{ ' while looking into ' + industry + ' businesses' if industry else '' }}{{ ' in ' + city if city else '' }} and I was really impressed by what you're doing.

I did notice, though, that {{ business_name }} doesn't seem to have a website yet — and in today's world, that's a huge opportunity you might be leaving on the table.

Here's why having a professional website matters:

  - Customers search online first — a website makes sure they find YOU, not a competitor.
  - It builds instant credibility and trust before someone even walks through the door.
  - It works 24/7 — showcasing your services, collecting inquiries, and driving business even when you're closed.
  - A Google Business Profile is great, but a website gives you full control of your brand story.

I specialize in building clean, modern, mobile-friendly websites tailored specifically for businesses like yours. The whole process is simple and hands-off for you — I handle everything from design to launch.

If this is something you'd be open to exploring, I'd love to have a quick chat — no pressure at all. Just a friendly conversation to see if it'd be a good fit.

{{ 'You can reach me at ' + sender_phone + ' or ' if sender_phone else '' }}Feel free to reply to this email anytime.

Best regards,
{{ sender_name }}{% if sender_website %}
{{ sender_website }}{% endif %}""",
            is_default=True,
        )
        db.session.add(default_template)

        followup_template = EmailTemplate(
            name="Gentle Follow-Up",
            subject="Following up — website for {{ business_name }}",
            body="""Hi{{ ' ' + contact_name if contact_name else '' }},

I reached out recently about building a professional website for {{ business_name }}, and I just wanted to circle back in case my message got buried.

I totally understand how busy things get — running a business is no small feat!

Just to recap, here's what I typically set up for businesses like yours:

  - A polished, mobile-friendly website that looks great on any device
  - Basic SEO so people in {{ city if city else 'your area' }} can actually find you on Google
  - A simple contact form so potential customers can reach out easily
  - Fast loading times and professional design that reflects your brand

There's absolutely no pressure — I just figured it was worth a quick follow-up in case it's something you'd find valuable.

If you'd like to chat for a few minutes, I'm happy to walk you through what the process looks like. Completely free, no strings attached.

Cheers,
{{ sender_name }}{% if sender_phone %}
{{ sender_phone }}{% endif %}{% if sender_website %}
{{ sender_website }}{% endif %}""",
            is_default=False,
        )
        db.session.add(followup_template)

    db.session.commit()


with app.app_context():
    db.create_all()
    seed_defaults()


# ---------------------------------------------------------------------------
# Email sending engine
# ---------------------------------------------------------------------------

def render_email(template_body, template_subject, contact, settings):
    """Render a Jinja2 template string with contact + sender variables."""
    context = {
        "business_name": contact.business_name,
        "contact_name": contact.contact_name,
        "email": contact.email,
        "industry": contact.industry,
        "city": contact.city,
        "notes": contact.notes,
        "sender_name": settings.sender_name,
        "sender_email": settings.sender_email,
        "sender_phone": settings.sender_phone,
        "sender_website": settings.sender_website,
    }
    rendered_subject = Template(template_subject).render(**context)
    rendered_body = Template(template_body).render(**context)
    return rendered_subject, rendered_body


def send_email(contact, template, settings):
    """Send a single email via SMTP. Returns (success: bool, error: str|None)."""
    subject, body = render_email(template.body, template.subject, contact, settings)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.sender_name} <{settings.sender_email}>"
    msg["To"] = contact.email

    plain_part = MIMEText(body, "plain")
    html_body = body.replace("\n", "<br>")
    html_part = MIMEText(f"<div style='font-family:sans-serif;line-height:1.6'>{html_body}</div>", "html")
    msg.attach(plain_part)
    msg.attach(html_part)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.sender_email, contact.email, msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    total = Contact.query.count()
    sent = Contact.query.filter_by(status="sent").count()
    pending = Contact.query.filter_by(status="pending").count()
    replied = Contact.query.filter_by(status="replied").count()
    converted = Contact.query.filter_by(status="converted").count()
    failed_emails = EmailLog.query.filter_by(status="failed").count()
    recent_logs = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(10).all()
    return render_template(
        "dashboard.html",
        stats={"total": total, "sent": sent, "pending": pending, "replied": replied, "converted": converted, "failed": failed_emails},
        recent_logs=recent_logs,
    )


@app.route("/contacts")
def contacts_page():
    return render_template("contacts.html")


@app.route("/templates")
def templates_page():
    return render_template("templates.html")


@app.route("/settings")
def settings_page():
    return render_template("settings.html")


# ---------------------------------------------------------------------------
# API — Contacts
# ---------------------------------------------------------------------------

@app.route("/api/contacts", methods=["GET"])
def api_get_contacts():
    status_filter = request.args.get("status")
    query = Contact.query.order_by(Contact.created_at.desc())
    if status_filter and status_filter != "all":
        query = query.filter_by(status=status_filter)
    contacts = query.all()
    return jsonify([c.to_dict() for c in contacts])


@app.route("/api/contacts", methods=["POST"])
def api_create_contact():
    data = request.json
    if not data.get("business_name") or not data.get("email"):
        return jsonify({"error": "Business name and email are required"}), 400
    contact = Contact(
        business_name=data["business_name"],
        contact_name=data.get("contact_name", ""),
        email=data["email"],
        industry=data.get("industry", ""),
        city=data.get("city", ""),
        notes=data.get("notes", ""),
    )
    db.session.add(contact)
    db.session.commit()
    return jsonify(contact.to_dict()), 201


@app.route("/api/contacts/<int:contact_id>", methods=["PUT"])
def api_update_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    data = request.json
    for field in ("business_name", "contact_name", "email", "industry", "city", "notes", "status"):
        if field in data:
            setattr(contact, field, data[field])
    db.session.commit()
    return jsonify(contact.to_dict())


@app.route("/api/contacts/<int:contact_id>", methods=["DELETE"])
def api_delete_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    EmailLog.query.filter_by(contact_id=contact.id).delete()
    db.session.delete(contact)
    db.session.commit()
    return jsonify({"ok": True})


@app.route("/api/contacts/bulk", methods=["POST"])
def api_bulk_create_contacts():
    """Accept a list of contacts to create at once."""
    data = request.json
    if not isinstance(data, list):
        return jsonify({"error": "Expected a JSON array"}), 400
    created = []
    for item in data:
        if not item.get("business_name") or not item.get("email"):
            continue
        contact = Contact(
            business_name=item["business_name"],
            contact_name=item.get("contact_name", ""),
            email=item["email"],
            industry=item.get("industry", ""),
            city=item.get("city", ""),
            notes=item.get("notes", ""),
        )
        db.session.add(contact)
        created.append(contact)
    db.session.commit()
    return jsonify({"created": len(created)}), 201


# ---------------------------------------------------------------------------
# API — Send emails
# ---------------------------------------------------------------------------

@app.route("/api/send/<int:contact_id>", methods=["POST"])
def api_send_one(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    settings = Settings.query.first()
    if not settings or not settings.smtp_username:
        return jsonify({"error": "SMTP settings not configured"}), 400

    template_id = request.json.get("template_id") if request.json else None
    if template_id:
        template = EmailTemplate.query.get(template_id)
    else:
        template = EmailTemplate.query.filter_by(is_default=True).first()
    if not template:
        return jsonify({"error": "No email template found"}), 400

    success, error = send_email(contact, template, settings)
    log = EmailLog(contact_id=contact.id, subject=template.subject, status="sent" if success else "failed", error_message=error)
    db.session.add(log)
    if success:
        contact.status = "sent"
        contact.sent_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify({"success": success, "error": error})


@app.route("/api/send/batch", methods=["POST"])
def api_send_batch():
    """Send to all pending contacts."""
    settings = Settings.query.first()
    if not settings or not settings.smtp_username:
        return jsonify({"error": "SMTP settings not configured"}), 400

    data = request.json or {}
    template_id = data.get("template_id")
    if template_id:
        template = EmailTemplate.query.get(template_id)
    else:
        template = EmailTemplate.query.filter_by(is_default=True).first()
    if not template:
        return jsonify({"error": "No email template found"}), 400

    contacts = Contact.query.filter_by(status="pending").all()
    results = {"sent": 0, "failed": 0, "errors": []}
    for contact in contacts:
        success, error = send_email(contact, template, settings)
        log = EmailLog(contact_id=contact.id, subject=template.subject, status="sent" if success else "failed", error_message=error)
        db.session.add(log)
        if success:
            contact.status = "sent"
            contact.sent_at = datetime.now(timezone.utc)
            results["sent"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({"business": contact.business_name, "error": error})
    db.session.commit()
    return jsonify(results)


@app.route("/api/preview", methods=["POST"])
def api_preview_email():
    """Preview a rendered email without sending it."""
    data = request.json
    settings = Settings.query.first()
    template_id = data.get("template_id")
    if template_id:
        template = EmailTemplate.query.get(template_id)
    else:
        template = EmailTemplate.query.filter_by(is_default=True).first()
    if not template:
        return jsonify({"error": "No template found"}), 400

    dummy_contact = Contact(
        business_name=data.get("business_name", "Acme Coffee Shop"),
        contact_name=data.get("contact_name", ""),
        email=data.get("email", "example@test.com"),
        industry=data.get("industry", ""),
        city=data.get("city", ""),
    )
    subject, body = render_email(template.body, template.subject, dummy_contact, settings)
    return jsonify({"subject": subject, "body": body})


# ---------------------------------------------------------------------------
# API — Templates
# ---------------------------------------------------------------------------

@app.route("/api/templates", methods=["GET"])
def api_get_templates():
    templates = EmailTemplate.query.order_by(EmailTemplate.created_at.desc()).all()
    return jsonify([t.to_dict() for t in templates])


@app.route("/api/templates", methods=["POST"])
def api_create_template():
    data = request.json
    if not data.get("name") or not data.get("subject") or not data.get("body"):
        return jsonify({"error": "Name, subject, and body are required"}), 400
    tmpl = EmailTemplate(name=data["name"], subject=data["subject"], body=data["body"], is_default=data.get("is_default", False))
    if tmpl.is_default:
        EmailTemplate.query.update({"is_default": False})
    db.session.add(tmpl)
    db.session.commit()
    return jsonify(tmpl.to_dict()), 201


@app.route("/api/templates/<int:template_id>", methods=["PUT"])
def api_update_template(template_id):
    tmpl = EmailTemplate.query.get_or_404(template_id)
    data = request.json
    for field in ("name", "subject", "body", "is_default"):
        if field in data:
            setattr(tmpl, field, data[field])
    if tmpl.is_default:
        EmailTemplate.query.filter(EmailTemplate.id != tmpl.id).update({"is_default": False})
    db.session.commit()
    return jsonify(tmpl.to_dict())


@app.route("/api/templates/<int:template_id>", methods=["DELETE"])
def api_delete_template(template_id):
    tmpl = EmailTemplate.query.get_or_404(template_id)
    db.session.delete(tmpl)
    db.session.commit()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# API — Settings
# ---------------------------------------------------------------------------

@app.route("/api/settings", methods=["GET"])
def api_get_settings():
    settings = Settings.query.first()
    return jsonify(settings.to_dict() if settings else {})


@app.route("/api/settings", methods=["PUT"])
def api_update_settings():
    settings = Settings.query.first()
    if not settings:
        settings = Settings()
        db.session.add(settings)
    data = request.json
    for field in ("smtp_server", "smtp_port", "smtp_username", "smtp_password", "sender_name", "sender_email", "sender_phone", "sender_website"):
        if field in data:
            setattr(settings, field, data[field])
    db.session.commit()
    return jsonify(settings.to_dict())


@app.route("/api/settings/test", methods=["POST"])
def api_test_smtp():
    """Send a test email to verify SMTP settings."""
    settings = Settings.query.first()
    if not settings or not settings.smtp_username:
        return jsonify({"success": False, "error": "SMTP settings not configured"}), 400
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.smtp_username, settings.smtp_password)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ---------------------------------------------------------------------------
# API — Logs
# ---------------------------------------------------------------------------

@app.route("/api/logs", methods=["GET"])
def api_get_logs():
    logs = EmailLog.query.order_by(EmailLog.sent_at.desc()).limit(100).all()
    return jsonify([l.to_dict() for l in logs])


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
