from pydantic import BaseModel
from fastapi import Request


class UserInfo(BaseModel):
    email: str
    name: str


async def get_current_user(request: Request) -> UserInfo:
    raw_email = request.headers.get("X-Goog-Authenticated-User-Email", "")
    email = raw_email.split(":", 1)[-1] if ":" in raw_email else raw_email
    if not email:
        email = "local.dev@alza.cz"
    return UserInfo(email=email, name=email.split("@")[0])
