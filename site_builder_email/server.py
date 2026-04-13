"""HTTP server for the outreach dashboard."""

from __future__ import annotations

import json
import mimetypes
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from site_builder_email.drafting import build_email_draft
from site_builder_email.mailer import load_smtp_settings, send_email
from site_builder_email.storage import Database, utc_now


PACKAGE_DIR = Path(__file__).resolve().parent
STATIC_DIR = PACKAGE_DIR / "static"
DEFAULT_DB_PATH = Path.cwd() / "data" / "outreach.db"


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload).encode("utf-8")


class OutreachHandler(BaseHTTPRequestHandler):
    database = Database(os.getenv("OUTREACH_DB_PATH", DEFAULT_DB_PATH))

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/leads":
            self._send_json({"leads": self.database.list_leads()})
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/leads":
            self._create_lead()
            return

        match = re.fullmatch(r"/api/leads/(\d+)/(draft|send)", parsed.path)
        if not match:
            self._send_json({"error": "Route not found."}, HTTPStatus.NOT_FOUND)
            return

        lead_id = int(match.group(1))
        action = match.group(2)

        if action == "draft":
            self._generate_draft(lead_id)
            return
        if action == "send":
            self._send_lead_email(lead_id)
            return

        self._send_json({"error": "Unsupported action."}, HTTPStatus.BAD_REQUEST)

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        match = re.fullmatch(r"/api/leads/(\d+)", parsed.path)
        if not match:
            self._send_json({"error": "Route not found."}, HTTPStatus.NOT_FOUND)
            return

        lead_id = int(match.group(1))
        try:
            payload = self._read_json_body()
            lead = self.database.update_lead(lead_id, payload)
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"lead": lead})

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._write_standard_headers("application/json")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Keep server logs concise."""
        super().log_message(format, *args)

    def _create_lead(self) -> None:
        try:
            payload = self._read_json_body()
            lead = self.database.create_lead(payload)
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return

        self._send_json({"lead": lead}, HTTPStatus.CREATED)

    def _generate_draft(self, lead_id: int) -> None:
        lead = self.database.get_lead(lead_id)
        if lead is None:
            self._send_json({"error": "Lead not found."}, HTTPStatus.NOT_FOUND)
            return

        sender_name = os.getenv("SMTP_FROM_NAME", "Your Name").strip() or "Your Name"
        draft = build_email_draft(lead, sender_name=sender_name)
        updated = self.database.update_lead(
            lead_id,
            {
                "draft_subject": draft["subject"],
                "draft_body": draft["body"],
                "status": "ready_to_review",
            },
        )
        self._send_json({"lead": updated})

    def _send_lead_email(self, lead_id: int) -> None:
        lead = self.database.get_lead(lead_id)
        if lead is None:
            self._send_json({"error": "Lead not found."}, HTTPStatus.NOT_FOUND)
            return
        if lead["do_not_contact"]:
            self._send_json(
                {"error": "This lead is marked as do not contact."},
                HTTPStatus.BAD_REQUEST,
            )
            return
        if not lead["draft_subject"] or not lead["draft_body"]:
            self._send_json(
                {"error": "Generate or enter an email draft before sending."},
                HTTPStatus.BAD_REQUEST,
            )
            return

        try:
            settings = load_smtp_settings()
            send_email(
                settings=settings,
                recipient=lead["email"],
                subject=lead["draft_subject"],
                body=lead["draft_body"],
            )
            updated = self.database.update_lead(
                lead_id,
                {
                    "status": "sent",
                    "last_sent_at": utc_now(),
                },
            )
        except ValueError as error:
            self._send_json({"error": str(error)}, HTTPStatus.BAD_REQUEST)
            return
        except Exception as error:  # pragma: no cover - external SMTP failures
            self._send_json(
                {"error": f"Failed to send email: {error}"},
                HTTPStatus.BAD_GATEWAY,
            )
            return

        self._send_json({"lead": updated})

    def _serve_static(self, request_path: str) -> None:
        path = request_path
        if path in ("", "/"):
            path = "/index.html"

        candidate = (STATIC_DIR / path.lstrip("/")).resolve()
        if STATIC_DIR not in candidate.parents and candidate != STATIC_DIR:
            self._send_json({"error": "Invalid path."}, HTTPStatus.BAD_REQUEST)
            return
        if not candidate.exists() or candidate.is_dir():
            self._send_json({"error": "Page not found."}, HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(candidate.name)
        content_type = content_type or "application/octet-stream"
        payload = candidate.read_bytes()
        self.send_response(HTTPStatus.OK)
        self._write_standard_headers(content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json_body(self) -> dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw_body = self.rfile.read(content_length) if content_length else b"{}"
        try:
            data = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Request body must be valid JSON.") from error
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self._write_standard_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _write_standard_headers(self, content_type: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")


def run() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    server = ThreadingHTTPServer((host, port), OutreachHandler)
    print(f"Dashboard running on http://{host}:{port}")
    server.serve_forever()

