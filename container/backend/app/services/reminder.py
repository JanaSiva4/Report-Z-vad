import requests
from fastapi import HTTPException
from app.config import settings


def send_teams_reminder(row: dict) -> None:
    if not settings.teams_reminder_webhook:
        raise HTTPException(status_code=503, detail="Teams webhook neni nakonfigurovan.")

    hours = row.get("hours_open")
    hours_text = f"{int(hours)} hodin" if hours is not None else "neznámá doba"

    sheets_link = f"\n\n📋 **[Otevřít tabulku a aktualizovat stav]({settings.sheets_url})**" if settings.sheets_url else ""

    message = (
        f"⏰ **PŘIPOMÍNKA: Nevyřešená závada ({hours_text})**\n\n"
        f"📅 Nahlášeno: {row.get('reported_at', '-')}\n"
        f"🔧 Technologie: {row.get('technology', '-')}\n"
        f"📍 Místo: {row.get('location', '-')}\n"
        f"🚨 Priorita: {row.get('priority', '-')}\n"
        f"📝 Popis: {row.get('description', '-')}\n"
        f"👤 Nahlásil: {row.get('reported_by', '-')}\n"
        f"📊 Stav: {row.get('status', '-')}"
        f"{sheets_link}"
    )

    payload = {"text": message}

    try:
        response = requests.post(
            settings.teams_reminder_webhook,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Teams zprava se nepodarila odeslat: {exc}") from exc
