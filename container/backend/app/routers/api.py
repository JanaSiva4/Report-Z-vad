from fastapi import APIRouter, Depends, HTTPException

from app.auth import UserInfo, get_current_user
from app.config import settings
from app.models.tickets import DashboardLogin, TicketCreate
from app.services.dashboard import load_dashboard
from app.services.reminder import send_teams_reminder
from app.services.tickets import submit_ticket


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
    submit_ticket(ticket)
    return {"status": "ok"}



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
