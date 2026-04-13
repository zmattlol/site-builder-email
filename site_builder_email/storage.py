"""SQLite storage for outreach leads and draft state."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEAD_FIELDS = {
    "business_name",
    "contact_name",
    "email",
    "google_profile_url",
    "business_type",
    "location",
    "offer_summary",
    "observed_gap",
    "benefits_focus",
    "notes",
    "draft_subject",
    "draft_body",
    "status",
    "do_not_contact",
    "last_sent_at",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_name TEXT NOT NULL,
                    contact_name TEXT NOT NULL DEFAULT '',
                    email TEXT NOT NULL,
                    google_profile_url TEXT NOT NULL DEFAULT '',
                    business_type TEXT NOT NULL DEFAULT '',
                    location TEXT NOT NULL DEFAULT '',
                    offer_summary TEXT NOT NULL DEFAULT '',
                    observed_gap TEXT NOT NULL DEFAULT '',
                    benefits_focus TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    draft_subject TEXT NOT NULL DEFAULT '',
                    draft_body TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    do_not_contact INTEGER NOT NULL DEFAULT 0,
                    last_sent_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def list_leads(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM leads ORDER BY updated_at DESC, id DESC"
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get_lead(self, lead_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM leads WHERE id = ?", (lead_id,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def create_lead(self, payload: dict[str, Any]) -> dict[str, Any]:
        created_at = utc_now()
        values = {
            "business_name": str(payload.get("business_name", "")).strip(),
            "contact_name": str(payload.get("contact_name", "")).strip(),
            "email": str(payload.get("email", "")).strip(),
            "google_profile_url": str(payload.get("google_profile_url", "")).strip(),
            "business_type": str(payload.get("business_type", "")).strip(),
            "location": str(payload.get("location", "")).strip(),
            "offer_summary": str(payload.get("offer_summary", "")).strip(),
            "observed_gap": str(payload.get("observed_gap", "")).strip(),
            "benefits_focus": str(payload.get("benefits_focus", "")).strip(),
            "notes": str(payload.get("notes", "")).strip(),
            "draft_subject": str(payload.get("draft_subject", "")).strip(),
            "draft_body": str(payload.get("draft_body", "")).strip(),
            "status": str(payload.get("status", "draft")).strip() or "draft",
            "do_not_contact": 1 if payload.get("do_not_contact") else 0,
        }

        if not values["business_name"]:
            raise ValueError("Business name is required.")
        if not values["email"]:
            raise ValueError("Contact email is required.")

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO leads (
                    business_name,
                    contact_name,
                    email,
                    google_profile_url,
                    business_type,
                    location,
                    offer_summary,
                    observed_gap,
                    benefits_focus,
                    notes,
                    draft_subject,
                    draft_body,
                    status,
                    do_not_contact,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["business_name"],
                    values["contact_name"],
                    values["email"],
                    values["google_profile_url"],
                    values["business_type"],
                    values["location"],
                    values["offer_summary"],
                    values["observed_gap"],
                    values["benefits_focus"],
                    values["notes"],
                    values["draft_subject"],
                    values["draft_body"],
                    values["status"],
                    values["do_not_contact"],
                    created_at,
                    created_at,
                ),
            )
            lead_id = cursor.lastrowid

        lead = self.get_lead(int(lead_id))
        if lead is None:
            raise RuntimeError("Failed to create lead.")
        return lead

    def update_lead(self, lead_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        for key, value in payload.items():
            if key not in LEAD_FIELDS:
                continue
            if key == "do_not_contact":
                updates[key] = 1 if value else 0
            elif value is None:
                updates[key] = ""
            else:
                updates[key] = str(value).strip()

        if not updates:
            lead = self.get_lead(lead_id)
            if lead is None:
                raise ValueError("Lead not found.")
            return lead

        updates["updated_at"] = utc_now()
        columns = ", ".join(f"{key} = ?" for key in updates.keys())
        parameters = list(updates.values()) + [lead_id]

        with self._connect() as connection:
            cursor = connection.execute(
                f"UPDATE leads SET {columns} WHERE id = ?", parameters
            )
            if cursor.rowcount == 0:
                raise ValueError("Lead not found.")

        lead = self.get_lead(lead_id)
        if lead is None:
            raise ValueError("Lead not found.")
        return lead

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["do_not_contact"] = bool(data["do_not_contact"])
        return data

