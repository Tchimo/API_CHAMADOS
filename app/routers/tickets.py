from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.dependencies import DbSession, get_current_user, require_staff
from app.models import SLA_HOURS, Ticket, TicketHistory, TicketPriority, TicketStatus, User, UserRole, utcnow
from app.schemas import HistoryOut, MetricsOut, TicketCreate, TicketOut, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["Chamados"])
CurrentUser = Annotated[User, Depends(get_current_user)]


def visible_query(user: User):
    return select(Ticket) if user.role in (UserRole.agent, UserRole.admin) else select(Ticket).where(Ticket.customer_id == user.id)


def get_ticket(db: Session, ticket_id: int, user: User) -> Ticket:
    ticket = db.scalar(visible_query(user).where(Ticket.id == ticket_id))
    if not ticket:
        raise HTTPException(404, "Chamado não encontrado")
    return ticket


def record(db: Session, ticket: Ticket, actor: User, action: str, old=None, new=None):
    db.add(TicketHistory(ticket_id=ticket.id, actor_id=actor.id, action=action, old_value=str(old) if old is not None else None, new_value=str(new) if new is not None else None))


@router.post("", response_model=TicketOut, status_code=201)
def create_ticket(data: TicketCreate, db: DbSession, current: CurrentUser):
    now = utcnow()
    ticket = Ticket(**data.model_dump(), customer_id=current.id, due_at=now + timedelta(hours=SLA_HOURS[data.priority]))
    db.add(ticket)
    db.flush()
    record(db, ticket, current, "created", new=ticket.status.value)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(db: DbSession, current: CurrentUser, status_filter: TicketStatus | None = Query(default=None, alias="status"), priority: TicketPriority | None = None, category: str | None = None, assignee_id: int | None = None, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    query = visible_query(current)
    if status_filter: query = query.where(Ticket.status == status_filter)
    if priority: query = query.where(Ticket.priority == priority)
    if category: query = query.where(Ticket.category == category)
    if assignee_id: query = query.where(Ticket.assignee_id == assignee_id)
    return list(db.scalars(query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit)).all())


@router.get("/metrics/summary", response_model=MetricsOut, dependencies=[Depends(require_staff)])
def metrics(db: DbSession):
    counts = {key.value: db.scalar(select(func.count()).select_from(Ticket).where(Ticket.status == key)) or 0 for key in TicketStatus}
    overdue = db.scalar(select(func.count()).select_from(Ticket).where(Ticket.due_at < utcnow(), Ticket.status.not_in([TicketStatus.resolved, TicketStatus.closed]))) or 0
    return {"total": sum(counts.values()), **counts, "overdue": overdue}


@router.get("/{ticket_id}", response_model=TicketOut)
def read_ticket(ticket_id: int, db: DbSession, current: CurrentUser):
    return get_ticket(db, ticket_id, current)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, data: TicketUpdate, db: DbSession, current: CurrentUser):
    ticket = get_ticket(db, ticket_id, current)
    if current.role == UserRole.customer and any(value is not None for key, value in data.model_dump().items() if key not in ("description",)):
        raise HTTPException(403, "Cliente só pode atualizar a descrição do chamado")
    changes = data.model_dump(exclude_unset=True)
    if current.role == UserRole.customer: changes = {"description": changes["description"]} if "description" in changes else {}
    for key, value in changes.items():
        old = getattr(ticket, key)
        if key == "status" and current.role == UserRole.customer and value not in (TicketStatus.closed,):
            raise HTTPException(403, "Cliente não pode alterar este status")
        setattr(ticket, key, value)
        if old != value: record(db, ticket, current, f"updated_{key}", old, value)
    if "priority" in changes:
        ticket.due_at = ticket.created_at + timedelta(hours=SLA_HOURS[ticket.priority])
    if ticket.status in (TicketStatus.resolved, TicketStatus.closed) and ticket.resolved_at is None: ticket.resolved_at = utcnow()
    db.commit(); db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}/history", response_model=list[HistoryOut])
def ticket_history(ticket_id: int, db: DbSession, current: CurrentUser):
    get_ticket(db, ticket_id, current)
    return list(db.scalars(select(TicketHistory).where(TicketHistory.ticket_id == ticket_id).order_by(TicketHistory.created_at)).all())
