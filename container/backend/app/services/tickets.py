import requests
from fastapi import HTTPException

from app.config import settings
from app.models.tickets import TicketCreate


def submit_ticket(ticket: TicketCreate) -> None:
    if not settings.webhook_url:
        raise HTTPException(status_code=503, detail="Webhook pro odeslani zavady neni nakonfigurovany.")

    payload = ticket.model_dump()
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.post(settings.webhook_url, json=payload, timeout=30)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Ticket se nepodarilo odeslat: {exc}") from exc

    if response.status_code not in {200, 201, 202}:
        raise HTTPException(status_code=502, detail=f"Odeslani selhalo se statusem {response.status_code}")

