from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from app.dependencies import DbSession
from app.models import User
from app.schemas import LoginRequest, Token, UserCreate, UserOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: DbSession):
    if db.scalar(select(User).where(User.email == data.email.lower())):
        raise HTTPException(409, "E-mail já cadastrado")
    user = User(name=data.name, email=data.email.lower(), password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: DbSession):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-mail ou senha inválidos")
    return {"access_token": create_access_token(str(user.id)), "token_type": "bearer"}
