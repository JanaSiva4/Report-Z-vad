from datetime import datetime, timezone
import re
import unicodedata

from fastapi import APIRouter, Depends, Header, HTTPException

from app.auth import UserInfo, get_current_user
from app.config import settings
from app.models.tickets import DashboardLogin, TeamsReply, TicketCreate
from app.services.dashboard import load_dashboard
from app.services.reminder import send_teams_reminder
from app.services.shift_report import build_shift_summary
from app.services.tickets import submit_ticket
from app.services.store import update_ticket_by_teams_id


router = APIRouter(prefix="/api")


@router.get("/me")
async def me(user: UserInfo = Depends(get_current_user)):
    return user


@router.get("/options")
async def options():
    return {
        "departments": [
            "baleni F1", "baleni F2", "AS", "nakladka F1", "nakladka F2",
            "doplnovani F2", "SPO", "BPO", "VS prijem", "VS potvrzovani",
            "VS baleni", "VS pick AS", "VS nakladka", "Specialista AS",
            "Specialista IT", "Vedeni LC", "Jine / Other",
        ],
        "technologies": [
            "AS", "TMT", "Innotech", "Knapp", "SSI", "ElVy", "Robopal",
            "Ropaso", "Intralox", "Ranpak closer", "Lantech erector",
            "Gaty", "Budova", "Jine / Other",
        ],
        "priorities": ["Low", "Medium", "High"],
    }


@router.post("/tickets")
async def create_ticket(ticket: TicketCreate):
    return {"status": "ok", **submit_ticket(ticket)}



@router.post("/dashboard/login")
async def dashboard_login(payload: DashboardLogin):
    if not settings.dashboard_password:
        raise HTTPException(status_code=503, detail="Dashboard password neni nastaveny.")
    if payload.password.strip() != settings.dashboard_password.strip():
        raise HTTPException(status_code=401, detail="Nespravne heslo.")
    return {"status": "ok"}


@router.get("/dashboard")
async def dashboard(days: str = "30", technology: str = "Vse", priority: str = "Vse"):
    return load_dashboard(days=days, technology=technology, priority=priority)



@router.post("/dashboard/remind")
async def remind(row: dict):
    send_teams_reminder(row)
    return {"status": "ok"}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower())
    return normalized.encode("ascii", "ignore").decode("ascii")


def _plain_text(value: str) -> str:
    return re.sub(r"<[^>]+>", " ", value).strip()


@router.post("/integrations/teams-reply")
async def teams_reply(payload: TeamsReply, x_api_key: str = Header(default="")):
    if settings.webhook_api_key and x_api_key != settings.webhook_api_key:
        raise HTTPException(status_code=401, detail="Neplatny API klic.")

    text = _plain_text(payload.message)
    normalized = _normalize(text)
    now = datetime.now(timezone.utc)

    update = {"last_reply": text, "last_reply_author": payload.author}
    if any(word in normalized for word in ["vyreseno", "hotovo", "opraveno", "resolved", "done", "fixed", "completed", "jede"]):
        update.update({"status": "Vyřešeno", "solved_at": now, "solution": text})
    elif any(word in normalized for word in ["servis", "ceka dil", "objednano", "waiting", "pending", "ordered", "v reseni", "ceka na servis"]):
        update.update({"status": "V řešení", "solution": text})

    if not update_ticket_by_teams_id(payload.teams_id, update):
        raise HTTPException(status_code=404, detail="Zavada s timto Teams ID nebyla nalezena.")

    return {"status": "ok"}


@router.get("/reports/shift-summary")
async def shift_summary(x_api_key: str = Header(default="")):
    if settings.webhook_api_key and x_api_key != settings.webhook_api_key:
        raise HTTPException(status_code=401, detail="Neplatny API klic.")
    return build_shift_summary()
