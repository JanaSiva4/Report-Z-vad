from app.services.store import update_ticket_by_id_or_teams_id, utc_now


def mark_ticket_reminded(row: dict, reminded_by: str = "") -> dict:
    reminded_at = utc_now()
    update = {
        "reminded": True,
        "reminded_at": reminded_at,
        "reminded_by": reminded_by,
    }
    updated = update_ticket_by_id_or_teams_id(
        str(row.get("id") or ""),
        str(row.get("teams_id") or ""),
        update,
    )
    return {"status": "ok", "updated": updated, "reminded_at": reminded_at.isoformat()}
