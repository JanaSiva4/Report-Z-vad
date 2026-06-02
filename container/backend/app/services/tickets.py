import requests
from fastapi import HTTPException

from app.config import settings
from app.models.tickets import TicketCreate
from app.services.attachments import store_ticket_attachments
from app.services.store import create_ticket_record, update_ticket


def submit_ticket(ticket: TicketCreate) -> dict:
    ticket_data = ticket.model_dump()
    incoming_attachments = ticket_data.pop("attachments", [])
    record = create_ticket_record({**ticket_data, "attachments": []})
    stored_attachments = store_ticket_attachments(record["id"], incoming_attachments)
    if stored_attachments:
        update_ticket(record["id"], {"attachments": stored_attachments})

    if not settings.webhook_url:
        return {"id": record["id"], "attachments": stored_attachments, "notification": "skipped"}

    payload = {**ticket_data, "attachments": stored_attachments, "ticket_id": record["id"]}
    headers = {"X-API-Key": settings.webhook_api_key} if settings.webhook_api_key else None
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.post(settings.webhook_url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Ticket je ulozeny, ale notifikace se nepodarila odeslat: {exc}") from exc

    if response.status_code not in {200, 201, 202}:
        raise HTTPException(status_code=502, detail=f"Ticket je ulozeny, ale notifikace selhala se statusem {response.status_code}")

    teams_id = ""
    try:
        body = response.json()
        teams_id = str(body.get("teams_id") or body.get("id") or "")
    except ValueError:
        body = {}

    if teams_id:
        update_ticket(record["id"], {"teams_id": teams_id})

    return {"id": record["id"], "teams_id": teams_id, "notification": "sent"}
