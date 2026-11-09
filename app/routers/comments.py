from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.dependencies import DbSession, get_current_user
from app.models import Comment, Ticket, User, UserRole
from app.schemas import CommentCreate, CommentOut

router = APIRouter(prefix="/tickets/{ticket_id}/comments", tags=["Comentários"])


@router.get("", response_model=list[CommentOut])
def list_comments(ticket_id: int, db: DbSession, current: Annotated[User, Depends(get_current_user)]):
    ticket = db.get(Ticket, ticket_id)
    if not ticket or (current.role == UserRole.customer and ticket.customer_id != current.id): raise HTTPException(404, "Chamado não encontrado")
    query = select(Comment).where(Comment.ticket_id == ticket_id)
    if current.role == UserRole.customer: query = query.where(Comment.is_internal.is_(False))
    return list(db.scalars(query.order_by(Comment.created_at)).all())


@router.post("", response_model=CommentOut, status_code=201)
def add_comment(ticket_id: int, data: CommentCreate, db: DbSession, current: Annotated[User, Depends(get_current_user)]):
    ticket = db.get(Ticket, ticket_id)
    if not ticket or (current.role == UserRole.customer and ticket.customer_id != current.id): raise HTTPException(404, "Chamado não encontrado")
    if data.is_internal and current.role == UserRole.customer: raise HTTPException(403, "Clientes não podem criar comentários internos")
    comment = Comment(**data.model_dump(), ticket_id=ticket_id, author_id=current.id)
    db.add(comment); db.commit(); db.refresh(comment)
    return comment
