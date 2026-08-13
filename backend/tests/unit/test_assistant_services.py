import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.asset_service import AssetService
from app.services.ticket_service import TicketService
from app.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_asset_and_ticket_service_extensions(db: AsyncSession):
    # Setup test user and asset
    auth_service = AuthService(db)
    user = await auth_service.register_user(
        username="tech_service",
        email="tech_service@test.com",
        password="password123",
        role="Technician",
    )

    asset_service = AssetService(db)
    asset = await asset_service.create_asset(
        asset_in=type(
            "AssetCreateMock",
            (),
            {
                "name": "Generator 500",
                "description": "Backup Diesel Generator",
                "sku": "GEN-500",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "status": "operational",
            },
        )()
    )

    # Test search assets
    found_assets = await asset_service.search_assets(query="Generator")
    assert len(found_assets) == 1
    assert found_assets[0].sku == "GEN-500"

    # Create ticket
    ticket_service = TicketService(db)
    ticket = await ticket_service.create_ticket(
        title="Check Fuel Filter",
        description="Inspect diesel fuel filter assembly",
        technician_id=user.id,
        asset_id=asset.id,
        priority="high",
    )
    assert ticket.status == "open"

    # Start service
    ticket = await ticket_service.start_service(ticket.id)
    assert ticket.status == "in_progress"

    # Add service notes and images
    ticket = await ticket_service.add_service_notes(ticket.id, "Filter clean, replaced gasket")
    assert "Filter clean" in ticket.description

    ticket = await ticket_service.upload_service_images(ticket.id, ["http://img1.jpg"])
    assert "http://img1.jpg" in ticket.description

    # Search tickets
    tickets_found = await ticket_service.search_tickets(query="Fuel Filter")
    assert len(tickets_found) == 1

    # Complete service
    ticket = await ticket_service.complete_service(ticket.id)
    assert ticket.status == "completed"
