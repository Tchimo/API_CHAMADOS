from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models import TicketPriority, TicketStatus, UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.customer


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TicketCreate(BaseModel):
    title: str = Field(min_length=5, max_length=180)
    description: str = Field(min_length=10)
    category: str = Field(min_length=2, max_length=80)
    priority: TicketPriority = TicketPriority.medium


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=180)
    description: str | None = Field(default=None, min_length=10)
    category: str | None = Field(default=None, min_length=2, max_length=80)
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    assignee_id: int | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    priority: TicketPriority
    status: TicketStatus
    customer_id: int
    assignee_id: int | None
    due_at: datetime
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    is_internal: bool = False


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    body: str
    is_internal: bool
    ticket_id: int
    author_id: int
    created_at: datetime


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    actor_id: int
    action: str
    old_value: str | None
    new_value: str | None
    created_at: datetime


class MetricsOut(BaseModel):
    total: int
    open: int
    in_progress: int
    waiting_customer: int
    resolved: int
    closed: int
    overdue: int
