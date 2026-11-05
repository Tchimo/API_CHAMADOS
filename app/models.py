from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UserRole(str, Enum):
    customer = "customer"
    agent = "agent"
    admin = "admin"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    waiting_customer = "waiting_customer"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


SLA_HOURS = {TicketPriority.low: 72, TicketPriority.medium: 24, TicketPriority.high: 8, TicketPriority.critical: 2}


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.customer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="customer", foreign_keys="Ticket.customer_id")
    assigned_tickets: Mapped[list["Ticket"]] = relationship(back_populates="assignee", foreign_keys="Ticket.assignee_id")
    comments: Mapped[list["Comment"]] = relationship(back_populates="author")


class Ticket(Base):
    __tablename__ = "tickets"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), index=True)
    priority: Mapped[TicketPriority] = mapped_column(default=TicketPriority.medium, index=True)
    status: Mapped[TicketStatus] = mapped_column(default=TicketStatus.open, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    due_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    customer: Mapped[User] = relationship(back_populates="tickets", foreign_keys=[customer_id])
    assignee: Mapped[User | None] = relationship(back_populates="assigned_tickets", foreign_keys=[assignee_id])
    comments: Mapped[list["Comment"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")
    history: Mapped[list["TicketHistory"]] = relationship(back_populates="ticket", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[str] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ticket: Mapped[Ticket] = relationship(back_populates="comments")
    author: Mapped[User] = relationship(back_populates="comments")


class TicketHistory(Base):
    __tablename__ = "ticket_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id"))
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(80))
    old_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ticket: Mapped[Ticket] = relationship(back_populates="history")
