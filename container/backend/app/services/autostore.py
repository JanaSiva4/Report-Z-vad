from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone

from app.models.tickets import AutoStoreEmail
from app.services.store import update_ticket, upsert_ticket_record


def _normalize(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _parse_event_time(text: str) -> datetime | None:
    if not text:
        return None
    for line in text.splitlines():
        if "Time of Event" in line:
            value = line.split("Time of Event", 1)[-1].strip(" :\t")
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
    return None


def _parse_title(subject: str) -> tuple[str, str]:
    subject_norm = subject.lower()
    if "manual system stop" in subject_norm or "manual action" in subject_norm:
        return "Manual System Stop Alert", "Manual System Stop"
    if "system stop" in subject_norm:
        return "System Stop Alert", "System Stop"
    return "AutoStore Alert", "AutoStore"


def _parse_fields(email: AutoStoreEmail) -> dict[str, str]:
    text = _normalize(email.text or email.html)
    subject = _normalize(email.subject)
    alert_title, stop_type = _parse_title(subject)

    grid = ""
    description = ""
    event_time = None

    grid_match = re.search(r"\bGrid\b\s*[:\n\r ]+\s*(.+?)(?:\n[A-Z][a-zA-Z ]+\n|\nDescription\b|\nTime of Event\b|$)", text, re.S)
    if grid_match:
        grid = grid_match.group(1).strip()

    desc_match = re.search(r"\bDescription\b\s*[:\n\r ]+\s*(.+?)(?:\nTime of Event\b|\nDetails\b|$)", text, re.S)
    if desc_match:
        description = desc_match.group(1).strip()

    event_time = _parse_event_time(text) or None

    return {
        "alert_title": alert_title,
        "stop_type": stop_type,
        "grid": grid,
        "description": description,
        "event_time": event_time.isoformat() if event_time else "",
        "from_email": email.from_email.strip(),
    }


def _external_id(payload: dict[str, str]) -> str:
    raw = "|".join(
        [
            payload.get("alert_title", ""),
            payload.get("stop_type", ""),
            payload.get("grid", ""),
            payload.get("event_time", ""),
            payload.get("description", ""),
        ]
    )
    return "autostore-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


def submit_autostore_email(email: AutoStoreEmail) -> dict:
    payload = _parse_fields(email)
    ticket_id = _external_id(payload)
    reported_by = payload["from_email"] or "noreply-cubeanalytics@autostoresystem.com"
    location = payload["grid"] or "AutoStore"
    description = payload["description"] or payload["alert_title"]
    note = f"{payload['stop_type']} | {payload['alert_title']}"
    record = {
        "id": ticket_id,
        "reported_by": reported_by,
        "department": "AutoStore",
        "technology": "AutoStore",
        "location": location,
        "priority": "High",
        "description": description,
        "note": note,
        "attachments": [],
        "status": "Otevřené",
        "source": "autostore-email",
        "teams_id": "",
        "created_at": payload["event_time"] or datetime.now(timezone.utc).isoformat(),
    }
    upsert_ticket_record(ticket_id, record)
    update_ticket(ticket_id, {
        "status": "Otevřené",
        "solution": "",
        "technician": "",
        "note": note,
    })
    return {
        "status": "ok",
        "ticket_id": ticket_id,
        "external_id": ticket_id,
        "payload": payload,
    }
