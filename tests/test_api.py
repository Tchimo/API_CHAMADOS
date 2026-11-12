import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"
from fastapi.testclient import TestClient
from app.database import Base, engine
from app.main import app

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_register_login_and_create_ticket():
    response = client.post("/api/v1/auth/register", json={"name":"Ana Cliente","email":"ana@example.com","password":"senha-segura-123"})
    assert response.status_code == 201
    login = client.post("/api/v1/auth/login", json={"email":"ana@example.com","password":"senha-segura-123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    ticket = client.post("/api/v1/tickets", headers={"Authorization": f"Bearer {token}"}, json={"title":"Não consigo acessar o sistema","description":"O login retorna erro desde esta manhã.","category":"acesso","priority":"high"})
    assert ticket.status_code == 201
    assert ticket.json()["status"] == "open"


def test_unauthenticated_is_rejected():
    assert client.get("/api/v1/tickets").status_code == 401
