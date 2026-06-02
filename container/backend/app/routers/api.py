from datetime import datetime, timezone
import re
import unicodedata

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, RedirectResponse

from app.auth import UserInfo, get_current_user
from app.config import settings
from app.models.tickets import DashboardLogin, TeamsReply, TicketCreate, TicketUpdate
from app.services.attachments import signed_attachment_url
from app.services.dashboard import load_dashboard, load_ticket_list
from app.services.reminder import mark_ticket_reminded
from app.services.sheets_import import import_csv_content
from app.services.shift_report import build_shift_summary
from app.services.store import delete_ticket_record, get_ticket_record, update_ticket, update_ticket_by_teams_id
from app.services.tickets import submit_ticket


router = APIRouter(prefix="/api")


@router.get("/me")
def me(user: UserInfo = Depends(get_current_user)):
    return user


@router.get("/options")
def options():
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
def create_ticket(ticket: TicketCreate):
    return {"status": "ok", **submit_ticket(ticket)}


@router.get("/tickets")
def tickets(limit: int = 300):
    return load_ticket_list(limit=limit)


@router.patch("/tickets/{ticket_id}")
def change_ticket(ticket_id: str, payload: TicketUpdate, user: UserInfo = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    update = {
        "status": payload.status,
        "solution": payload.solution.strip(),
        "technician": payload.technician.strip() or user.email,
    }
    if payload.status in {"V řešení", "Čeká"}:
        update["reacted_at"] = now
    if payload.status == "Vyřešeno":
        update["solved_at"] = now
        update.setdefault("reacted_at", now)
    update_ticket(ticket_id, update)
    return {"status": "ok"}


@router.delete("/tickets/{ticket_id}")
def delete_ticket(ticket_id: str, user: UserInfo = Depends(get_current_user)):
    delete_ticket_record(ticket_id)
    return {"status": "ok"}


@router.get("/tickets/{ticket_id}/attachments/{attachment_index}")
def open_attachment(ticket_id: str, attachment_index: int, user: UserInfo = Depends(get_current_user)):
    ticket = get_ticket_record(ticket_id)
    attachments = ticket.get("attachments") if isinstance(ticket.get("attachments"), list) else []
    if attachment_index < 0 or attachment_index >= len(attachments):
        raise HTTPException(status_code=404, detail="Priloha nebyla nalezena.")
    attachment = attachments[attachment_index]
    local_path = str(attachment.get("local_path") or "")
    if local_path:
        return FileResponse(local_path, filename=str(attachment.get("name") or "priloha"))
    return RedirectResponse(signed_attachment_url(attachment))


@router.post("/dashboard/login")
def dashboard_login(payload: DashboardLogin, user: UserInfo = Depends(get_current_user)):
    if settings.dashboard_password and payload.password.strip() != settings.dashboard_password.strip():
        raise HTTPException(status_code=401, detail="Nespravne heslo.")
    return {"status": "ok", "user": user.email}


@router.get("/dashboard")
def dashboard(days: str = "30", technology: str = "Vse", priority: str = "Vse"):
    return load_dashboard(days=days, technology=technology, priority=priority)


@router.post("/dashboard/import-csv")
async def import_dashboard_csv(
    password: str = Form(default=""),
    file: UploadFile = File(...),
    user: UserInfo = Depends(get_current_user),
):
    if settings.dashboard_password and password.strip() != settings.dashboard_password.strip():
        raise HTTPException(status_code=401, detail="Nespravne heslo.")
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nahrajte CSV soubor.")
    return import_csv_content(await file.read())


@router.post("/dashboard/remind")
def remind(row: dict, user: UserInfo = Depends(get_current_user)):
    return mark_ticket_reminded(row, user.email)


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
    elif any(word in normalized for word in ["servis", "ceka dil", "objednano", "waiting", "pending", "ordered", "ceka na servis"]):
        update.update({"status": "Čeká", "solution": text})
    elif any(word in normalized for word in ["v reseni", "resim", "opravuji", "in progress"]):
        update.update({"status": "V řešení", "solution": text})

    if not update_ticket_by_teams_id(payload.teams_id, update):
        raise HTTPException(status_code=404, detail="Zavada s timto Teams ID nebyla nalezena.")

    return {"status": "ok"}


@router.get("/reports/shift-summary")
async def shift_summary(x_api_key: str = Header(default="")):
    if settings.webhook_api_key and x_api_key != settings.webhook_api_key:
        raise HTTPException(status_code=401, detail="Neplatny API klic.")
    return build_shift_summary()


