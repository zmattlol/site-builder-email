from __future__ import annotations

import os
import re
import smtplib
import sqlite3
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, abort, current_app, flash, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "outreach.db"

DEFAULT_OFFER = "design, setup, copywriting, contact forms, and basic SEO"
DEFAULT_BENEFITS = (
    "- Turn profile views into customer inquiries\n"
    "- Share services, pricing, and hours clearly\n"
    "- Build trust with photos, testimonials, and FAQs"
)
DEFAULT_CTA = "would you be open to a quick 10-minute chat this week?"
DEFAULT_SUBJECT_TEMPLATE = "Quick website idea for {{business_name}}"
DEFAULT_BODY_TEMPLATE = (
    "Hi {{contact_name_or_business}},\n\n"
    "I came across {{business_name}}{{city_suffix}} and noticed you may not have a dedicated website yet.\n"
    "I help local businesses launch personalized sites that are simple to manage and built to convert visitors into customers.\n\n"
    "{{benefits}}\n\n"
    "I can handle the full setup for you, including {{offer}}.\n\n"
    "If this sounds helpful, {{cta}}\n\n"
    "Best,\n"
    "{{sender_name}}"
)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LEAD_STATUSES = ("new", "contacted", "replied", "uninterested")


def create_app() -> Flask:
    load_dotenv()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-in-env")
    app.config["DATABASE"] = os.getenv("OUTREACH_DB_PATH", str(DEFAULT_DB_PATH))

    with app.app_context():
        init_db()

    @app.teardown_appcontext
    def close_db_connection(_error: BaseException | None) -> None:
        close_db()

    @app.get("/")
    def dashboard() -> str:
        db = get_db()
        settings = get_settings(db)
        leads = db.execute(
            """
            SELECT
                l.*,
                e.status AS last_email_status,
                e.error_message AS last_error,
                e.sent_at AS last_sent_at,
                (
                    SELECT COUNT(*)
                    FROM email_logs x
                    WHERE x.lead_id = l.id AND x.status = 'sent'
                ) AS sent_count
            FROM leads l
            LEFT JOIN email_logs e
                ON e.id = (
                    SELECT id
                    FROM email_logs z
                    WHERE z.lead_id = l.id
                    ORDER BY z.id DESC
                    LIMIT 1
                )
            ORDER BY l.created_at DESC, l.id DESC
            """
        ).fetchall()
        return render_template(
            "dashboard.html",
            leads=leads,
            settings=settings,
            statuses=LEAD_STATUSES,
            placeholders=sorted(email_context_for_preview({}, {}).keys()),
        )

    @app.post("/settings")
    def save_settings() -> Any:
        db = get_db()
        smtp_port = parse_port(request.form.get("smtp_port", ""))
        values = {
            "smtp_host": request.form.get("smtp_host", "").strip(),
            "smtp_port": smtp_port,
            "smtp_username": request.form.get("smtp_username", "").strip(),
            "smtp_password": request.form.get("smtp_password", "").strip(),
            "smtp_use_tls": 1 if request.form.get("smtp_use_tls") == "on" else 0,
            "from_email": request.form.get("from_email", "").strip(),
            "reply_to": request.form.get("reply_to", "").strip(),
            "sender_name": request.form.get("sender_name", "").strip() or "Your Name",
            "offer": request.form.get("offer", "").strip() or DEFAULT_OFFER,
            "benefits": request.form.get("benefits", "").strip() or DEFAULT_BENEFITS,
            "cta": request.form.get("cta", "").strip() or DEFAULT_CTA,
            "subject_template": request.form.get("subject_template", "").strip() or DEFAULT_SUBJECT_TEMPLATE,
            "body_template": request.form.get("body_template", "").strip() or DEFAULT_BODY_TEMPLATE,
        }
        db.execute(
            """
            UPDATE settings
            SET
                smtp_host = :smtp_host,
                smtp_port = :smtp_port,
                smtp_username = :smtp_username,
                smtp_password = :smtp_password,
                smtp_use_tls = :smtp_use_tls,
                from_email = :from_email,
                reply_to = :reply_to,
                sender_name = :sender_name,
                offer = :offer,
                benefits = :benefits,
                cta = :cta,
                subject_template = :subject_template,
                body_template = :body_template,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            values,
        )
        db.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/leads")
    def add_lead() -> Any:
        business_name = request.form.get("business_name", "").strip()
        contact_name = request.form.get("contact_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        city = request.form.get("city", "").strip()
        google_profile_url = request.form.get("google_profile_url", "").strip()
        notes = request.form.get("notes", "").strip()

        if not business_name or not email:
            flash("Business name and email are required.", "error")
            return redirect(url_for("dashboard"))

        if not EMAIL_PATTERN.match(email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("dashboard"))

        db = get_db()
        db.execute(
            """
            INSERT INTO leads (business_name, contact_name, email, city, google_profile_url, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (business_name, contact_name, email, city, google_profile_url, notes),
        )
        db.commit()
        flash("Lead added.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/leads/<int:lead_id>/preview")
    def preview_email(lead_id: int) -> str:
        db = get_db()
        lead = get_lead_or_404(db, lead_id)
        settings = get_settings(db)
        subject, body = render_email_for_lead(lead, settings)
        return render_template("preview.html", lead=lead, subject=subject, body=body)

    @app.post("/leads/<int:lead_id>/send")
    def send_single_email(lead_id: int) -> Any:
        sent, error = send_outreach_to_lead(lead_id)
        if sent:
            flash("Email sent successfully.", "success")
        else:
            flash(f"Email failed: {error}", "error")
        return redirect(url_for("dashboard"))

    @app.post("/campaign/send")
    def send_bulk_campaign() -> Any:
        lead_ids = request.form.getlist("lead_ids")
        if not lead_ids:
            flash("Select at least one lead to send.", "error")
            return redirect(url_for("dashboard"))

        successes = 0
        failures = 0
        for raw_id in lead_ids:
            try:
                lead_id = int(raw_id)
            except ValueError:
                continue
            sent, _ = send_outreach_to_lead(lead_id)
            if sent:
                successes += 1
            else:
                failures += 1

        flash(f"Campaign complete. Sent: {successes}, Failed: {failures}.", "success" if failures == 0 else "error")
        return redirect(url_for("dashboard"))

    @app.post("/leads/<int:lead_id>/status")
    def update_status(lead_id: int) -> Any:
        new_status = request.form.get("status", "").strip()
        if new_status not in LEAD_STATUSES:
            flash("Invalid status selected.", "error")
            return redirect(url_for("dashboard"))

        db = get_db()
        get_lead_or_404(db, lead_id)
        db.execute("UPDATE leads SET status = ? WHERE id = ?", (new_status, lead_id))
        db.commit()
        flash("Lead status updated.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/leads/<int:lead_id>/delete")
    def delete_lead(lead_id: int) -> Any:
        db = get_db()
        get_lead_or_404(db, lead_id)
        db.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        db.commit()
        flash("Lead deleted.", "success")
        return redirect(url_for("dashboard"))

    return app


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        connection = sqlite3.connect(current_app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db() -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            smtp_host TEXT NOT NULL DEFAULT '',
            smtp_port INTEGER NOT NULL DEFAULT 587,
            smtp_username TEXT NOT NULL DEFAULT '',
            smtp_password TEXT NOT NULL DEFAULT '',
            smtp_use_tls INTEGER NOT NULL DEFAULT 1,
            from_email TEXT NOT NULL DEFAULT '',
            reply_to TEXT NOT NULL DEFAULT '',
            sender_name TEXT NOT NULL DEFAULT 'Your Name',
            offer TEXT NOT NULL DEFAULT 'design, setup, copywriting, contact forms, and basic SEO',
            benefits TEXT NOT NULL DEFAULT '- Turn profile views into customer inquiries
- Share services, pricing, and hours clearly
- Build trust with photos, testimonials, and FAQs',
            cta TEXT NOT NULL DEFAULT 'would you be open to a quick 10-minute chat this week?',
            subject_template TEXT NOT NULL DEFAULT 'Quick website idea for {{business_name}}',
            body_template TEXT NOT NULL DEFAULT 'Hi {{contact_name_or_business}},

I came across {{business_name}}{{city_suffix}} and noticed you may not have a dedicated website yet.
I help local businesses launch personalized sites that are simple to manage and built to convert visitors into customers.

{{benefits}}

I can handle the full setup for you, including {{offer}}.

If this sounds helpful, {{cta}}

Best,
{{sender_name}}',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            contact_name TEXT NOT NULL DEFAULT '',
            email TEXT NOT NULL,
            city TEXT NOT NULL DEFAULT '',
            google_profile_url TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'new',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_contacted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE
        );
        """
    )

    existing = db.execute("SELECT id FROM settings WHERE id = 1").fetchone()
    if existing is None:
        db.execute("INSERT INTO settings (id) VALUES (1)")
    db.commit()


def get_settings(db: sqlite3.Connection) -> sqlite3.Row:
    settings = db.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    if settings is None:
        db.execute("INSERT INTO settings (id) VALUES (1)")
        db.commit()
        settings = db.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    return settings


def parse_port(value: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return 587
    return port if 1 <= port <= 65535 else 587


def get_lead_or_404(db: sqlite3.Connection, lead_id: int) -> sqlite3.Row:
    lead = db.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    if lead is None:
        abort(404)
    return lead


def normalize_benefits(text: str) -> str:
    lines: list[str] = []
    for raw_line in (text or "").splitlines():
        cleaned = raw_line.strip()
        if not cleaned:
            continue
        if cleaned.startswith("-"):
            cleaned = cleaned[1:].strip()
        lines.append(f"- {cleaned}")
    if not lines:
        lines = DEFAULT_BENEFITS.splitlines()
    return "\n".join(lines)


def row_value(record: dict[str, Any] | sqlite3.Row, key: str) -> str:
    if isinstance(record, dict):
        return str(record.get(key, "")).strip()
    if key in record.keys():
        return str(record[key]).strip()
    return ""


def email_context_for_preview(lead: dict[str, Any] | sqlite3.Row, settings: dict[str, Any] | sqlite3.Row) -> dict[str, str]:
    business_name = row_value(lead, "business_name")
    contact_name = row_value(lead, "contact_name")
    city = row_value(lead, "city")
    notes = row_value(lead, "notes")
    google_profile_url = row_value(lead, "google_profile_url")
    city_suffix = f" in {city}" if city else ""
    contact_name_or_business = contact_name or business_name or "there"

    if isinstance(settings, dict):
        sender_name = str(settings.get("sender_name", "")).strip() or "Your Name"
        offer = str(settings.get("offer", "")).strip() or DEFAULT_OFFER
        cta = str(settings.get("cta", "")).strip() or DEFAULT_CTA
        benefits = normalize_benefits(str(settings.get("benefits", "")))
    else:
        sender_name = str(settings["sender_name"]).strip() or "Your Name"
        offer = str(settings["offer"]).strip() or DEFAULT_OFFER
        cta = str(settings["cta"]).strip() or DEFAULT_CTA
        benefits = normalize_benefits(str(settings["benefits"]))

    return {
        "business_name": business_name,
        "contact_name": contact_name,
        "contact_name_or_business": contact_name_or_business,
        "city": city,
        "city_suffix": city_suffix,
        "notes": notes,
        "google_profile_url": google_profile_url,
        "offer": offer,
        "benefits": benefits,
        "cta": cta,
        "sender_name": sender_name,
    }


def render_tokens(raw_template: str, context: dict[str, str]) -> str:
    rendered = raw_template
    for key, value in context.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered


def render_email_for_lead(lead: sqlite3.Row, settings: sqlite3.Row) -> tuple[str, str]:
    context = email_context_for_preview(lead, settings)
    subject_template = settings["subject_template"] or DEFAULT_SUBJECT_TEMPLATE
    body_template = settings["body_template"] or DEFAULT_BODY_TEMPLATE

    subject = render_tokens(subject_template, context).strip() or DEFAULT_SUBJECT_TEMPLATE
    body = render_tokens(body_template, context).strip() or DEFAULT_BODY_TEMPLATE
    return subject, body


def send_outreach_to_lead(lead_id: int) -> tuple[bool, str]:
    db = get_db()
    lead = get_lead_or_404(db, lead_id)
    settings = get_settings(db)
    subject, body = render_email_for_lead(lead, settings)

    status = "sent"
    error = ""
    try:
        send_email_via_smtp(
            to_email=lead["email"],
            subject=subject,
            body=body,
            settings=settings,
        )
        db.execute(
            "UPDATE leads SET status = 'contacted', last_contacted_at = CURRENT_TIMESTAMP WHERE id = ?",
            (lead_id,),
        )
    except Exception as exc:  # noqa: BLE001 - surface operational SMTP errors to UI.
        status = "failed"
        error = str(exc)

    db.execute(
        """
        INSERT INTO email_logs (lead_id, subject, body, status, error_message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (lead_id, subject, body, status, error if error else None),
    )
    db.commit()

    return status == "sent", error


def send_email_via_smtp(*, to_email: str, subject: str, body: str, settings: sqlite3.Row) -> None:
    smtp_host = settings["smtp_host"].strip()
    smtp_port = int(settings["smtp_port"] or 587)
    smtp_username = settings["smtp_username"].strip()
    smtp_password = settings["smtp_password"]
    smtp_use_tls = bool(settings["smtp_use_tls"])
    from_email = settings["from_email"].strip() or smtp_username
    reply_to = settings["reply_to"].strip()

    if not smtp_host:
        raise ValueError("SMTP host is required in settings.")
    if not from_email:
        raise ValueError("From email is required (or set SMTP username).")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    if reply_to:
        message["Reply-To"] = reply_to
    message.set_content(body)

    with smtplib.SMTP(host=smtp_host, port=smtp_port, timeout=30) as server:
        server.ehlo()
        if smtp_use_tls:
            server.starttls()
            server.ehlo()
        if smtp_username:
            server.login(smtp_username, smtp_password)
        server.send_message(message)


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
