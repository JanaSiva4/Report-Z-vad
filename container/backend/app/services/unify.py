from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import HTTPException

from app.config import settings
from app.services.store import get_ticket_record, update_ticket, upsert_ticket_record


STOPWORDS = {
    "stopped",
    "stop",
    "system stop",
    "manual stop",
    "manual system stop",
    "system stop alert",
    "manual system stop alert",
    "disconnected",
}


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", str(value or "").lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _field(item: dict[str, Any], *names: str) -> str:
    for name in names:
        value = item.get(name)
        if value not in (None, ""):
            return _clean(value)
    return ""


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        text = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y %H:%M",
            ):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("events", "items", "rows", "data", "results", "value"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    if any(payload.get(key) is not None for key in ("status", "mode", "systemMode", "errorCode", "grid", "timestamp")):
        return [payload]
    return []


def _is_stop_event(item: dict[str, Any]) -> bool:
    text = " ".join(
        _clean(_field(item, *names))
        for names in (
            ("subject", "title", "name", "eventType"),
            ("status", "state", "mode", "systemMode"),
            ("description", "message", "details", "errorMessage"),
            ("grid", "installation", "location"),
            ("errorCode", "error_code", "code"),
        )
    )
    normalized = _normalize_text(text)
    return any(word in normalized for word in STOPWORDS) or "xhandler_robot_error_failed" in normalized


def _parse_event(item: dict[str, Any]) -> dict[str, Any] | None:
    if not _is_stop_event(item):
        return None

    event_type = _field(item, "eventType", "subject", "title", "name")
    status = _field(item, "status", "state", "mode", "systemMode")
    error_code = _field(item, "errorCode", "error_code", "code")
    grid = _field(item, "grid", "installation", "location", "line")
    description = _field(item, "description", "message", "details", "errorMessage")
    timestamp_raw = _field(item, "timestamp", "createdAt", "created_at", "time", "startTime", "start_time", "eventTime", "receivedAt")
    event_dt = _parse_dt(timestamp_raw)

    kind = "Manual System Stop" if "manual" in _normalize_text(f"{event_type} {status} {description}") else "System Stop"
    if not event_type:
        event_type = f"{kind} Alert"

    return {
        "event_type": event_type,
        "kind": kind,
        "grid": grid or "AutoStore",
        "error_code": error_code,
        "description": description or error_code or event_type,
        "event_time": event_dt.isoformat() if event_dt else "",
        "source_id": _field(item, "id", "eventId", "event_id", "uuid"),
    }


def _external_id(event: dict[str, Any]) -> str:
    raw = "|".join(
        [
            event.get("kind", ""),
            event.get("grid", ""),
            event.get("error_code", ""),
            event.get("event_time", ""),
            event.get("description", ""),
            event.get("source_id", ""),
        ]
    )
    return "unify-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _ticket_payload(event: dict[str, Any]) -> dict[str, Any]:
    title = f"AutoStore {event.get('kind', 'Stop')}"
    note_bits = [event.get("kind", "AutoStore")]
    if event.get("error_code"):
        note_bits.append(event["error_code"])
    if event.get("source_id"):
        note_bits.append(f"ID {event['source_id']}")
    return {
        "id": _external_id(event),
        "reported_by": "unify-api@autostore",
        "department": "AutoStore",
        "technology": "AutoStore",
        "location": event.get("grid") or "AutoStore",
        "priority": "High",
        "description": event.get("description") or title,
        "note": " | ".join(note_bits),
        "attachments": [],
        "status": "Otevřené",
        "source": "unify-api",
        "teams_id": "",
        "created_at": event.get("event_time") or datetime.now(timezone.utc).isoformat(),
    }


def fetch_unify_payload() -> Any:
    if not settings.unify_api_url:
        raise ValueError("UNIFY_API_URL neni nakonfigurovany.")
    if not settings.unify_api_token:
        raise ValueError("UNIFY_API_TOKEN neni nakonfigurovany.")

    headers = {
        "API-Authorization": f"Token {settings.unify_api_token.strip()}",
        "Accept": "application/json",
    }
    session = requests.Session()
    session.trust_env = False
    response = session.get(settings.unify_api_url.strip(), headers=headers, timeout=45)
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        text = response.text.strip()
        if not text:
            raise ValueError("Uniify API vratilo praznou odpoved.") from exc
        try:
            return json.loads(text)
        except ValueError:
            raise ValueError("Uniify API nevratilo JSON.") from exc


def sync_unify_events() -> dict[str, Any]:
    payload = fetch_unify_payload()
    items = _extract_items(payload)
    created = 0
    updated = 0
    ignored = 0
    processed: list[str] = []

    for item in items:
        parsed = _parse_event(item)
        if not parsed:
            ignored += 1
            continue
        ticket_id = _external_id(parsed)
        record = _ticket_payload(parsed)
        try:
            get_ticket_record(ticket_id)
            updated += 1
        except HTTPException:
            created += 1
        upsert_ticket_record(ticket_id, record)
        update_ticket(ticket_id, {"status": "Otevřené", "solution": "", "technician": "", "note": record["note"]})
        processed.append(ticket_id)

    return {
        "status": "ok",
        "created": created,
        "updated": updated,
        "ignored": ignored,
        "processed": processed,
        "items_seen": len(items),
    }
