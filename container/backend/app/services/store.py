from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException

from app.config import settings


TICKETS_COLLECTION = "tickets"


def _client() -> firestore.Client:
    if not settings.gcp_project_id:
        raise HTTPException(status_code=503, detail="GCP_PROJECT_ID neni nakonfigurovany.")
    from google.cloud import firestore

    return firestore.Client(project=settings.gcp_project_id)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_ticket_record(data: dict[str, Any]) -> dict[str, Any]:
    db = _client()
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
    db.collection(TICKETS_COLLECTION).document(ticket_id).set(record)
    return record


def update_ticket(ticket_id: str, data: dict[str, Any]) -> None:
    db = _client()
    db.collection(TICKETS_COLLECTION).document(ticket_id).update({**data, "updated_at": utc_now()})


def update_ticket_by_teams_id(teams_id: str, data: dict[str, Any]) -> bool:
    from google.cloud.firestore_v1 import FieldFilter

    db = _client()
    docs = (
        db.collection(TICKETS_COLLECTION)
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


def list_ticket_records(limit: int = 1000) -> list[dict[str, Any]]:
    from google.cloud import firestore

    db = _client()
    docs = (
        db.collection(TICKETS_COLLECTION)
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
