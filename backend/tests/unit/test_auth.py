import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.core import security


@pytest.mark.asyncio
async def test_register_and_authenticate_user(db: AsyncSession):
    auth_service = AuthService(db)

    # 1. Register technician
    user = await auth_service.register_user(
        username="tech_tim",
        email="tim@enterprise.com",
        password="securepassword123",
        role="Technician"
    )
    assert user.id is not None
    assert user.username == "tech_tim"
    assert user.role == "Technician"
    assert security.verify_password("securepassword123", user.hashed_password)

    # 2. Authenticate technician
    authenticated_user = await auth_service.authenticate_user("tech_tim", "securepassword123")
    assert authenticated_user.id == user.id


@pytest.mark.asyncio
async def test_auth_api_routes(client: AsyncClient):
    # 1. Register via endpoint
    register_payload = {
        "username": "tech_bob",
        "email": "bob@enterprise.com",
        "password": "bobsecretpassword",
        "role": "Technician"
    }
    response = await client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "tech_bob"

    # 2. Login via endpoint
    login_payload = {
        "username": "tech_bob",
        "password": "bobsecretpassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
