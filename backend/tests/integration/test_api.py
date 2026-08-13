import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth_service import AuthService
from app.core import security


@pytest.mark.asyncio
async def test_complete_technician_flow(client: AsyncClient, db: AsyncSession):
    # 1. Register and Login to get Auth token
    auth_service = AuthService(db)
    user = await auth_service.register_user(
        username="tech_john",
        email="john@enterprise.com",
        password="password123",
        role="Technician"
    )
    
    access_token = security.create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role}
    )
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Update Location
    loc_payload = {"latitude": 37.7749, "longitude": -122.4194, "accuracy": 10.0}
    response = await client.post("/api/v1/location", json=loc_payload, headers=headers)
    assert response.status_code == 201

    # 3. Retrieve assets (Seeding is triggered inside AssetService when empty)
    response = await client.get(
        "/api/v1/assets/nearby?latitude=37.7749&longitude=-122.4194", headers=headers
    )
    assert response.status_code == 200
    assets = response.json()
    assert len(assets) > 0
    asset_id = assets[0]["id"]

    # 4. Create Ticket
    ticket_payload = {
        "title": "Water Leakage",
        "description": "Main water pump leaking at joint A",
        "asset_id": asset_id,
        "priority": "high"
    }
    response = await client.post("/api/v1/tickets", json=ticket_payload, headers=headers)
    assert response.status_code == 201
    ticket = response.json()
    assert ticket["title"] == "Water Leakage"
    ticket_id = ticket["id"]

    # 5. Get Ticket Summary
    response = await client.get(f"/api/v1/tickets/{ticket_id}/summary", headers=headers)
    assert response.status_code == 200
    summary = response.json()
    assert "summary" in summary

    # 6. Interact via Chat
    chat_payload = {
        "message": "Find nearby assets",
        "session_id": "session-test-id",
        "latitude": 37.7749,
        "longitude": -122.4194
    }
    response = await client.post("/api/v1/chat", json=chat_payload, headers=headers)
    assert response.status_code == 200
    chat_resp = response.json()
    assert "response" in chat_resp
    assert chat_resp["session_id"] == "session-test-id"

    # 7. Query Tickets via Chat
    chat_tickets_payload = {
        "message": "Show my tickets",
        "session_id": "session-test-id",
        "latitude": 37.7749,
        "longitude": -122.4194,
    }
    response = await client.post("/api/v1/chat", json=chat_tickets_payload, headers=headers)
    assert response.status_code == 200
    chat_resp_tickets = response.json()
    assert "response" in chat_resp_tickets
    assert chat_resp_tickets["session_id"] == "session-test-id"

