from __future__ import annotations

from datetime import datetime, timedelta, timezone
import csv
import hashlib
import io
import re

import requests

from app.config import settings
from app.services.store import upsert_ticket_record


def _field(row: dict, *names: str) -> str:
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def _parse_datetime(value: str):
    if not value:
        return None
    text = str(value)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
        for fmt in ("%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                pass
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone(timedelta(hours=1)))
    return parsed


def _sheet_csv_url() -> str:
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", settings.sheets_url)
    if not match:
        raise ValueError("Nelze zjistit ID spreadsheetu z SHEETS_URL")
    return f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv&gid=0"


def _ticket_id(row: dict) -> str:
    teams_id = _field(row, "ID Teams")
    if teams_id:
        return "teams-" + hashlib.sha1(teams_id.encode("utf-8")).hexdigest()
    raw = "|".join(
        [
            _field(row, "Čas nahlášení", "Cas nahlaseni"),
            _field(row, "Nahlásil", "Nahlasil"),
            _field(row, "Technologie"),
            _field(row, "Místo", "Misto"),
            _field(row, "Popis"),
        ]
    )
    return "sheet-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _iso_or_none(value: str):
    parsed = _parse_datetime(value)
    return parsed if parsed else None


def _to_record(row: dict) -> dict:
    reported_at = _iso_or_none(_field(row, "Čas nahlášení", "Cas nahlaseni"))
    reacted_at = _iso_or_none(_field(row, "Čas reakce", "Cas reakce"))
    solved_at = _iso_or_none(_field(row, "Čas vyřešení", "Cas vyreseni"))
    created_at = reported_at or datetime.utcnow()
    return {
        "source": "google-sheets-import",
        "created_at": created_at,
        "reacted_at": reacted_at,
        "solved_at": solved_at,
        "department": _field(row, "Oddělení", "Oddeleni"),
        "technology": _field(row, "Technologie"),
        "location": _field(row, "Místo", "Misto"),
        "priority": _field(row, "Priorita"),
        "description": _field(row, "Popis"),
        "note": _field(row, "Poznámka", "Poznamka"),
        "reported_by": _field(row, "Nahlásil", "Nahlasil"),
        "status": _field(row, "Stav", "Status"),
        "solution": _field(row, "Popis řešení", "Popis reseni"),
        "teams_id": _field(row, "ID Teams"),
        "attachment": _field(row, "Příloha", "Priloha"),
    }


def import_google_sheet_tickets() -> dict:
    if not settings.sheets_url:
        return {"enabled": False, "imported": 0}

    session = requests.Session()
    session.trust_env = False
    response = session.get(_sheet_csv_url(), timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
    imported = 0
    for row in reader:
        clean_row = {str(k).strip(): v for k, v in row.items() if k is not None}
        if not any(str(v or "").strip() for v in clean_row.values()):
            continue
        upsert_ticket_record(_ticket_id(clean_row), _to_record(clean_row))
        imported += 1
    return {"enabled": True, "imported": imported}
