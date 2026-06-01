from pydantic import BaseModel, Field


class Attachment(BaseModel):
    name: str
    data: str


class TicketCreate(BaseModel):
    reported_by: str = Field(min_length=1)
    department: str = Field(min_length=1)
    technology: str = Field(min_length=1)
    location: str = Field(min_length=1)
    priority: str = Field(pattern="^(Low|Medium|High)$")
    description: str = Field(min_length=1)
    note: str = ""
    attachments: list[Attachment] = []


class DashboardLogin(BaseModel):
    password: str


class TeamsReply(BaseModel):
    teams_id: str = Field(min_length=1)
    message: str = Field(min_length=1)
    author: str = ""
