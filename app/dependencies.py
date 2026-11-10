from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, UserRole
from app.security import decode_subject

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DbSession) -> User:
    subject = decode_subject(token)
    if not subject or not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    user = db.get(User, int(subject))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inválido")
    return user


def require_staff(current: Annotated[User, Depends(get_current_user)]) -> User:
    if current.role not in (UserRole.agent, UserRole.admin):
        raise HTTPException(status_code=403, detail="Acesso restrito à equipe de suporte")
    return current


def require_admin(current: Annotated[User, Depends(get_current_user)]) -> User:
    if current.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Acesso restrito a administradores")
    return current
