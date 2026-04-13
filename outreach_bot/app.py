import os
import sqlite3
import smtplib
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from email_service import generate_email_body, generate_subject

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

DB_PATH = os.path.join(os.path.dirname(__file__), "outreach.db")


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key   TEXT PRIMARY KEY,
                value TEXT
            );

            CREATE TABLE IF NOT EXISTS campaigns (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS leads (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id   INTEGER REFERENCES campaigns(id),
                business_name TEXT NOT NULL,
                contact_name  TEXT,
                email         TEXT NOT NULL,
                industry      TEXT,
                location      TEXT,
                notes         TEXT,
                status        TEXT NOT NULL DEFAULT 'pending',
                sent_at       TEXT,
                opened        INTEGER NOT NULL DEFAULT 0,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS email_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id     INTEGER REFERENCES leads(id),
                subject     TEXT,
                body        TEXT,
                status      TEXT,
                error       TEXT,
                sent_at     TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)


init_db()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_setting(key, default=""):
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )


def send_email(lead: dict, settings: dict) -> tuple[bool, str]:
    """Send one outreach email. Returns (success, error_message)."""
    smtp_host = settings.get("smtp_host", "")
    smtp_port = int(settings.get("smtp_port", 587))
    smtp_user = settings.get("smtp_user", "")
    smtp_pass = settings.get("smtp_pass", "")
    sender_name = settings.get("sender_name", "")
    sender_email = settings.get("sender_email", smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass]):
        return False, "SMTP settings are incomplete. Configure them in Settings."

    subject = generate_subject(lead)
    body_html = generate_email_body(lead, settings)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = lead["email"]

    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(sender_email, [lead["email"]], msg.as_string())
        return True, ""
    except Exception as exc:
        return False, str(exc)


def collect_settings():
    keys = [
        "smtp_host", "smtp_port", "smtp_user", "smtp_pass",
        "sender_name", "sender_email",
        "your_name", "your_title", "your_phone", "your_website",
        "service_blurb",
    ]
    return {k: get_setting(k) for k in keys}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    with get_db() as conn:
        total_leads   = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        sent_count    = conn.execute("SELECT COUNT(*) FROM leads WHERE status='sent'").fetchone()[0]
        pending_count = conn.execute("SELECT COUNT(*) FROM leads WHERE status='pending'").fetchone()[0]
        failed_count  = conn.execute("SELECT COUNT(*) FROM leads WHERE status='failed'").fetchone()[0]
        recent_leads  = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT 10"
        ).fetchall()
        campaigns     = conn.execute("SELECT * FROM campaigns ORDER BY created_at DESC").fetchall()
    return render_template(
        "dashboard.html",
        total_leads=total_leads,
        sent_count=sent_count,
        pending_count=pending_count,
        failed_count=failed_count,
        recent_leads=recent_leads,
        campaigns=campaigns,
    )


@app.route("/leads")
def leads():
    status_filter   = request.args.get("status", "all")
    campaign_filter = request.args.get("campaign", "all")
    search          = request.args.get("q", "")

    query  = "SELECT l.*, c.name as campaign_name FROM leads l LEFT JOIN campaigns c ON l.campaign_id=c.id WHERE 1=1"
    params = []

    if status_filter != "all":
        query += " AND l.status=?"
        params.append(status_filter)
    if campaign_filter != "all":
        query += " AND l.campaign_id=?"
        params.append(campaign_filter)
    if search:
        query += " AND (l.business_name LIKE ? OR l.email LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]

    query += " ORDER BY l.created_at DESC"

    with get_db() as conn:
        lead_rows  = conn.execute(query, params).fetchall()
        campaigns  = conn.execute("SELECT * FROM campaigns ORDER BY name").fetchall()

    return render_template(
        "leads.html",
        leads=lead_rows,
        campaigns=campaigns,
        status_filter=status_filter,
        campaign_filter=campaign_filter,
        search=search,
    )


@app.route("/leads/new", methods=["GET", "POST"])
def new_lead():
    with get_db() as conn:
        campaigns = conn.execute("SELECT * FROM campaigns ORDER BY name").fetchall()

    if request.method == "POST":
        data = request.form
        with get_db() as conn:
            conn.execute(
                """INSERT INTO leads
                   (campaign_id, business_name, contact_name, email, industry, location, notes)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    data.get("campaign_id") or None,
                    data["business_name"],
                    data.get("contact_name", ""),
                    data["email"],
                    data.get("industry", ""),
                    data.get("location", ""),
                    data.get("notes", ""),
                ),
            )
        flash("Lead added successfully!", "success")
        return redirect(url_for("leads"))

    return render_template("new_lead.html", campaigns=campaigns)


@app.route("/leads/<int:lead_id>")
def lead_detail(lead_id):
    with get_db() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
        logs = conn.execute(
            "SELECT * FROM email_log WHERE lead_id=? ORDER BY sent_at DESC", (lead_id,)
        ).fetchall()
    if not lead:
        flash("Lead not found.", "error")
        return redirect(url_for("leads"))
    settings = collect_settings()
    preview_html = generate_email_body(dict(lead), settings)
    preview_subject = generate_subject(dict(lead))
    return render_template(
        "lead_detail.html",
        lead=lead,
        logs=logs,
        preview_html=preview_html,
        preview_subject=preview_subject,
    )


@app.route("/leads/<int:lead_id>/send", methods=["POST"])
def send_to_lead(lead_id):
    with get_db() as conn:
        lead = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not lead:
        return jsonify({"ok": False, "error": "Lead not found"}), 404

    settings = collect_settings()
    success, error = send_email(dict(lead), settings)

    status  = "sent" if success else "failed"
    sent_at = datetime.utcnow().isoformat()

    with get_db() as conn:
        conn.execute(
            "UPDATE leads SET status=?, sent_at=? WHERE id=?",
            (status, sent_at, lead_id),
        )
        conn.execute(
            """INSERT INTO email_log(lead_id, subject, body, status, error, sent_at)
               VALUES (?,?,?,?,?,?)""",
            (
                lead_id,
                generate_subject(dict(lead)),
                generate_email_body(dict(lead), settings),
                status,
                error,
                sent_at,
            ),
        )

    if success:
        flash(f"Email sent to {lead['email']}!", "success")
    else:
        flash(f"Failed to send: {error}", "error")

    return redirect(url_for("lead_detail", lead_id=lead_id))


@app.route("/leads/<int:lead_id>/delete", methods=["POST"])
def delete_lead(lead_id):
    with get_db() as conn:
        conn.execute("DELETE FROM email_log WHERE lead_id=?", (lead_id,))
        conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
    flash("Lead deleted.", "success")
    return redirect(url_for("leads"))


@app.route("/campaigns/new", methods=["POST"])
def new_campaign():
    name = request.form.get("name", "").strip()
    if name:
        with get_db() as conn:
            conn.execute("INSERT INTO campaigns(name) VALUES(?)", (name,))
        flash(f'Campaign "{name}" created.', "success")
    return redirect(url_for("dashboard"))


@app.route("/bulk-send", methods=["POST"])
def bulk_send():
    """Send emails to all pending leads (or a specific campaign)."""
    campaign_id = request.form.get("campaign_id") or None
    settings    = collect_settings()

    query  = "SELECT * FROM leads WHERE status='pending'"
    params = []
    if campaign_id:
        query += " AND campaign_id=?"
        params.append(campaign_id)

    with get_db() as conn:
        pending = conn.execute(query, params).fetchall()

    sent_ok  = 0
    sent_err = 0

    for lead in pending:
        success, error = send_email(dict(lead), settings)
        status  = "sent" if success else "failed"
        sent_at = datetime.utcnow().isoformat()
        if success:
            sent_ok += 1
        else:
            sent_err += 1
        with get_db() as conn:
            conn.execute(
                "UPDATE leads SET status=?, sent_at=? WHERE id=?",
                (status, sent_at, lead["id"]),
            )
            conn.execute(
                """INSERT INTO email_log(lead_id, subject, body, status, error, sent_at)
                   VALUES (?,?,?,?,?,?)""",
                (
                    lead["id"],
                    generate_subject(dict(lead)),
                    generate_email_body(dict(lead), settings),
                    status,
                    error,
                    sent_at,
                ),
            )
        time.sleep(1.5)  # basic rate-limiting

    flash(f"Bulk send complete: {sent_ok} sent, {sent_err} failed.", "success" if not sent_err else "error")
    return redirect(url_for("dashboard"))


@app.route("/preview-email")
def preview_email():
    """Live AJAX preview of the email based on form fields."""
    lead = {
        "business_name": request.args.get("business_name", "Acme Co"),
        "contact_name":  request.args.get("contact_name", ""),
        "industry":      request.args.get("industry", ""),
        "location":      request.args.get("location", ""),
        "notes":         request.args.get("notes", ""),
    }
    settings = collect_settings()
    return jsonify({
        "subject": generate_subject(lead),
        "body":    generate_email_body(lead, settings),
    })


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        for key in request.form:
            set_setting(key, request.form[key])
        flash("Settings saved!", "success")
        return redirect(url_for("settings"))
    current = collect_settings()
    return render_template("settings.html", settings=current)


@app.route("/log")
def email_log():
    with get_db() as conn:
        logs = conn.execute(
            """SELECT el.*, l.business_name, l.email
               FROM email_log el
               LEFT JOIN leads l ON el.lead_id = l.id
               ORDER BY el.sent_at DESC LIMIT 200"""
        ).fetchall()
    return render_template("log.html", logs=logs)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
