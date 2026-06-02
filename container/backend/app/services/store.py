from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.config import settings
from app.services.attachments import delete_stored_attachments


LOCAL_TEST_PREFIX = "tickets_test_"
LOCAL_STORE_DIR = Path(__file__).resolve().parents[2] / ".local_test_store"
LOCAL_STORE_FILE = LOCAL_STORE_DIR / "tickets.json"


def _tickets_collection() -> str:
    return settings.firestore_collection.strip() or "tickets"


def _is_local_test_store() -> bool:
    return (
        os.getenv("LOCAL_TEST_MODE") == "1"
        or os.getenv("FIRESTORE_COLLECTION", "").startswith(LOCAL_TEST_PREFIX)
        or _tickets_collection().startswith(LOCAL_TEST_PREFIX)
        or LOCAL_STORE_FILE.exists()
    )


def _client():
    if not settings.gcp_project_id:
        raise HTTPException(status_code=503, detail="GCP_PROJECT_ID neni nakonfigurovany.")
    from google.cloud import firestore

    return firestore.Client(project=settings.gcp_project_id)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _local_read_all() -> list[dict[str, Any]]:
    if not LOCAL_STORE_FILE.exists():
        return []
    try:
        data = json.loads(LOCAL_STORE_FILE.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _local_write_all(rows: list[dict[str, Any]]) -> None:
    LOCAL_STORE_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_STORE_FILE.write_text(json.dumps(rows, ensure_ascii=False, default=_json_default, indent=2), encoding="utf-8")


def _local_upsert(record: dict[str, Any], merge: bool = False) -> None:
    rows = _local_read_all()
    for index, row in enumerate(rows):
        if row.get("id") == record["id"]:
            rows[index] = {**row, **record} if merge else record
            _local_write_all(rows)
            return
    rows.append(record)
    _local_write_all(rows)


def _local_get(ticket_id: str) -> dict[str, Any]:
    for row in _local_read_all():
        if row.get("id") == ticket_id:
            return row
    raise HTTPException(status_code=404, detail="Zavada nebyla nalezena.")


def _local_delete(ticket_id: str) -> None:
    rows = [row for row in _local_read_all() if row.get("id") != ticket_id]
    _local_write_all(rows)


def _local_list(limit: int = 1000) -> list[dict[str, Any]]:
    rows = sorted(_local_read_all(), key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return rows[:limit]


def create_ticket_record(data: dict[str, Any]) -> dict[str, Any]:
    ticket_id = uuid4().hex
    now = utc_now()
    record = {
        **data,
        "id": ticket_id,
        "status": data.get("status") or "",
        "teams_id": data.get("teams_id") or "",
        "created_at": now,
        "updated_at": now,
        "reacted_at": None,
        "solved_at": None,
        "solution": "",
        "source": data.get("source") or "app",
    }
    if _is_local_test_store():
        _local_upsert(record)
        return record

    db = _client()
    db.collection(_tickets_collection()).document(ticket_id).set(record)
    return record


def upsert_ticket_record(ticket_id: str, data: dict[str, Any]) -> None:
    now = utc_now()
    record = {
        **data,
        "id": ticket_id,
        "updated_at": now,
    }
    if _is_local_test_store():
        _local_upsert(record, merge=True)
        return

    db = _client()
    db.collection(_tickets_collection()).document(ticket_id).set(record, merge=True)


def update_ticket(ticket_id: str, data: dict[str, Any]) -> None:
    if _is_local_test_store():
        current = _local_get(ticket_id)
        update = {**data, "updated_at": utc_now()}
        if update.get("status") in {"V řešení", "Čeká", "Vyřešeno"} and not current.get("reacted_at"):
            update["reacted_at"] = utc_now()
        elif current.get("reacted_at") and "reacted_at" in update:
            update.pop("reacted_at")
        _local_upsert({**current, **update}, merge=False)
        return

    db = _client()
    ref = db.collection(_tickets_collection()).document(ticket_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Zavada nebyla nalezena.")
    current = snapshot.to_dict() or {}
    update = {**data, "updated_at": utc_now()}
    if update.get("status") in {"V řešení", "Čeká", "Vyřešeno"} and not current.get("reacted_at"):
        update["reacted_at"] = utc_now()
    elif current.get("reacted_at") and "reacted_at" in update:
        update.pop("reacted_at")
    ref.update(update)


def update_ticket_by_teams_id(teams_id: str, data: dict[str, Any]) -> bool:
    if _is_local_test_store():
        rows = _local_read_all()
        for index, row in enumerate(rows):
            if str(row.get("teams_id") or "") == teams_id:
                current = row
                update = {**data, "updated_at": utc_now()}
                if not current.get("reacted_at"):
                    update["reacted_at"] = utc_now()
                rows[index] = {**current, **update}
                _local_write_all(rows)
                return True
        return False

    from google.cloud.firestore_v1 import FieldFilter

    db = _client()
    docs = (
        db.collection(_tickets_collection())
        .where(filter=FieldFilter("teams_id", "==", teams_id))
        .limit(1)
        .stream()
    )
    for doc in docs:
        current = doc.to_dict() or {}
        update = {**data, "updated_at": utc_now()}
        if not current.get("reacted_at"):
            update["reacted_at"] = utc_now()
        doc.reference.update(update)
        return True
    return False


def update_ticket_by_id_or_teams_id(ticket_id: str, teams_id: str, data: dict[str, Any]) -> bool:
    if ticket_id:
        update_ticket(ticket_id, data)
        return True
    if teams_id:
        return update_ticket_by_teams_id(teams_id, data)
    return False


def get_ticket_record(ticket_id: str) -> dict[str, Any]:
    if _is_local_test_store():
        return _local_get(ticket_id)

    db = _client()
    snapshot = db.collection(_tickets_collection()).document(ticket_id).get()
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Zavada nebyla nalezena.")
    data = snapshot.to_dict() or {}
    data.setdefault("id", snapshot.id)
    return data


def delete_ticket_record(ticket_id: str) -> None:
    if _is_local_test_store():
        current = _local_get(ticket_id)
        attachments = current.get("attachments") if isinstance(current.get("attachments"), list) else []
        delete_stored_attachments(attachments)
        _local_delete(ticket_id)
        return

    db = _client()
    ref = db.collection(_tickets_collection()).document(ticket_id)
    snapshot = ref.get()
    if not snapshot.exists:
        raise HTTPException(status_code=404, detail="Zavada nebyla nalezena.")
    data = snapshot.to_dict() or {}
    attachments = data.get("attachments") if isinstance(data.get("attachments"), list) else []
    delete_stored_attachments(attachments)
    ref.delete()


def list_ticket_records(limit: int = 1000) -> list[dict[str, Any]]:
    if _is_local_test_store():
        return _local_list(limit=limit)

    from google.cloud import firestore

    db = _client()
    docs = (
        db.collection(_tickets_collection())
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    rows: list[dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict() or {}
        data.setdefault("id", doc.id)
        rows.append(data)
    return rows
