"""SMTP helpers for sending reviewed outreach emails."""

from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage


@dataclass
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    from_email: str
    from_name: str
    use_starttls: bool


def load_smtp_settings() -> SmtpSettings:
    host = os.getenv("SMTP_HOST", "").strip()
    username = os.getenv("SMTP_USERNAME", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
    from_name = os.getenv("SMTP_FROM_NAME", "Your Name").strip() or "Your Name"
    port = int(os.getenv("SMTP_PORT", "587"))
    use_starttls = os.getenv("SMTP_USE_STARTTLS", "true").strip().lower() != "false"

    missing = [
        name
        for name, value in (
            ("SMTP_HOST", host),
            ("SMTP_USERNAME", username),
            ("SMTP_PASSWORD", password),
            ("SMTP_FROM_EMAIL", from_email),
        )
        if not value
    ]
    if missing:
        raise ValueError(
            "Missing SMTP configuration: " + ", ".join(missing)
        )

    return SmtpSettings(
        host=host,
        port=port,
        username=username,
        password=password,
        from_email=from_email,
        from_name=from_name,
        use_starttls=use_starttls,
    )


def send_email(settings: SmtpSettings, recipient: str, subject: str, body: str) -> None:
    if not recipient.strip():
        raise ValueError("Recipient email is required.")
    if not subject.strip():
        raise ValueError("Email subject is required.")
    if not body.strip():
        raise ValueError("Email body is required.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.from_name} <{settings.from_email}>"
    message["To"] = recipient.strip()
    message.set_content(body)

    context = ssl.create_default_context()
    with smtplib.SMTP(settings.host, settings.port, timeout=30) as client:
        if settings.use_starttls:
            client.starttls(context=context)
        client.login(settings.username, settings.password)
        client.send_message(message)

