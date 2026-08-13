from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.agents.registry import tool_registry
from app.services.asset_service import AssetService
from app.services.ticket_service import TicketService
from app.services.location_service import LocationService
from app.services.memory_service import MemoryService
from app.core.exceptions import NotFoundException


def safe_int(val: Any, default: int = 0) -> int:
    """Safely convert any input value (int, str, dict) to an integer."""
    if isinstance(val, int):
        return val
    if isinstance(val, float):
        return int(val)
    if isinstance(val, str):
        try:
            return int(val)
        except Exception:
            return default
    if isinstance(val, dict):
        for v in val.values():
            if isinstance(v, (int, str)):
                try:
                    return int(v)
                except Exception:
                    pass
    return default


# --- Asset Tools ---

@tool_registry.register(
    name="list_assets",
    description="Retrieve list of all assets in the system database.",
    input_schema={
        "type": "object",
        "properties": {
            "skip": {"type": "integer", "default": 0},
            "limit": {"type": "integer", "default": 100},
        },
    },
)
async def list_assets_tool(skip: Any = 0, limit: Any = 100, db: AsyncSession = None) -> Dict[str, Any]:
    skip_val = safe_int(skip, 0)
    limit_val = safe_int(limit, 100)
    service = AssetService(db)
    assets = await service.list_assets(skip=skip_val, limit=limit_val)
    return {
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "sku": a.sku,
                "status": a.status,
                "latitude": a.latitude,
                "longitude": a.longitude,
            }
            for a in assets
        ]
    }


@tool_registry.register(
    name="get_asset",
    description="Look up full details of a specific asset by its asset ID.",
    input_schema={
        "type": "object",
        "properties": {
            "asset_id": {"type": "integer", "description": "Unique identifier of the target asset"}
        },
        "required": ["asset_id"],
    },
)
async def get_asset_tool(asset_id: Any, db: AsyncSession = None) -> Dict[str, Any]:
    asset_id_val = safe_int(asset_id, 1)
    service = AssetService(db)
    try:
        a = await service.get_asset(asset_id_val)
        return {
            "asset": {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "sku": a.sku,
                "status": a.status,
                "latitude": a.latitude,
                "longitude": a.longitude,
            }
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="search_assets",
    description="Search assets by text query or status filter.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term matching asset name, description, or SKU"},
            "status": {"type": "string", "description": "Asset operational status (e.g. operational, maintenance_required)"},
            "skip": {"type": "integer", "default": 0},
            "limit": {"type": "integer", "default": 100},
        },
    },
)
async def search_assets_tool(
    query: Optional[str] = None,
    status: Optional[str] = None,
    skip: Any = 0,
    limit: Any = 100,
    db: AsyncSession = None,
) -> Dict[str, Any]:
    skip_val = safe_int(skip, 0)
    limit_val = safe_int(limit, 100)
    service = AssetService(db)
    assets = await service.search_assets(query=query, status=status, skip=skip_val, limit=limit_val)
    return {
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "sku": a.sku,
                "status": a.status,
            }
            for a in assets
        ]
    }


@tool_registry.register(
    name="find_assets",
    description="Locate nearby assets within a specified geographic radius.",
    input_schema={
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "description": "Latitude coordinate"},
            "longitude": {"type": "number", "description": "Longitude coordinate"},
            "radius_meters": {"type": "number", "description": "Search radius in meters. Default is 50m."},
        },
        "required": ["latitude", "longitude"],
    },
)
async def find_assets_tool(
    latitude: float, longitude: float, radius_meters: float = 50.0, db: AsyncSession = None
) -> Dict[str, Any]:
    service = AssetService(db)
    assets = await service.find_nearby_assets(latitude, longitude, radius_meters)
    return {
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "sku": a.sku,
                "status": a.status,
                "latitude": a.latitude,
                "longitude": a.longitude,
            }
            for a in assets
        ]
    }


# Alias searchNearbyAssets to find_assets
@tool_registry.register(
    name="search_nearby_assets",
    description="Search for assets near given GPS coordinates.",
    input_schema={
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
            "radius_meters": {"type": "number", "default": 50.0},
        },
        "required": ["latitude", "longitude"],
    },
)
async def search_nearby_assets_tool(
    latitude: float, longitude: float, radius_meters: float = 50.0, db: AsyncSession = None
) -> Dict[str, Any]:
    return await find_assets_tool(latitude, longitude, radius_meters, db)


# --- Ticket Tools ---

@tool_registry.register(
    name="create_ticket",
    description="Create a new ticket for a specific asset.",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short title describing the issue"},
            "description": {"type": "string", "description": "Detailed problem description"},
            "asset_id": {"type": "integer", "description": "Target asset ID"},
            "priority": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium"},
        },
        "required": ["title", "description", "asset_id"],
    },
    requires_confirmation=True,
)
async def create_ticket_tool(
    title: str,
    description: str,
    asset_id: Any,
    priority: str = "medium",
    user_id: int = None,
    db: AsyncSession = None,
) -> Dict[str, Any]:
    asset_id_val = safe_int(asset_id, 1)
    service = TicketService(db)
    ticket = await service.create_ticket(
        title=title,
        description=description,
        technician_id=user_id,
        asset_id=asset_id_val,
        priority=priority,
    )
    return {
        "ticket_id": ticket.id,
        "title": ticket.title,
        "status": ticket.status,
        "priority": ticket.priority,
        "asset_id": ticket.asset_id,
        "message": f"Ticket #{ticket.id} created successfully.",
    }


@tool_registry.register(
    name="get_ticket",
    description="Look up full details of a specific ticket by its ID.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "Unique ID of the ticket"}
        },
        "required": ["ticket_id"],
    },
)
async def get_ticket_tool(ticket_id: Any, db: AsyncSession = None) -> Dict[str, Any]:
    ticket_id_val = safe_int(ticket_id, 1)
    service = TicketService(db)
    try:
        t = await service.get_ticket(ticket_id_val)
        asset_name = t.asset.name if t.asset else f"Asset #{t.asset_id}"
        return {
            "ticket": {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "asset_id": t.asset_id,
                "asset_name": asset_name,
                "technician_id": t.technician_id,
            },
            "summary": await service.summarize_ticket(ticket_id_val),
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="list_tickets",
    description="Retrieve list of all tickets or user's assigned tickets.",
    input_schema={
        "type": "object",
        "properties": {
            "my_tickets_only": {"type": "boolean", "default": False, "description": "If true, return only tickets assigned to current technician"},
            "skip": {"type": "integer", "default": 0},
            "limit": {"type": "integer", "default": 100},
        },
    },
)
async def list_tickets_tool(
    my_tickets_only: bool = False,
    skip: Any = 0,
    limit: Any = 100,
    user_id: int = None,
    db: AsyncSession = None,
) -> Dict[str, Any]:
    skip_val = safe_int(skip, 0)
    limit_val = safe_int(limit, 100)
    service = TicketService(db)
    if my_tickets_only and user_id:
        tickets = await service.list_my_tickets(user_id, skip=skip_val, limit=limit_val)
    else:
        tickets = await service.list_tickets(skip=skip_val, limit=limit_val)
    return {
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "asset_id": t.asset_id,
                "technician_id": t.technician_id,
            }
            for t in tickets
        ]
    }


@tool_registry.register(
    name="search_tickets",
    description="Search tickets by query string, status, priority, or asset ID.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Keyword to match title or description"},
            "status": {"type": "string", "description": "Filter by status (open, in_progress, completed, resolved, closed)"},
            "priority": {"type": "string", "description": "Filter by priority (low, medium, high, critical)"},
            "asset_id": {"type": "integer", "description": "ID of asset to filter tickets for"},
            "skip": {"type": "integer", "default": 0},
            "limit": {"type": "integer", "default": 100},
        },
    },
)
async def search_tickets_tool(
    query: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    asset_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = None,
) -> Dict[str, Any]:
    service = TicketService(db)
    tickets = await service.search_tickets(
        query=query, status=status, priority=priority, asset_id=asset_id, skip=skip, limit=limit
    )
    return {
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "asset_id": t.asset_id,
            }
            for t in tickets
        ]
    }


@tool_registry.register(
    name="find_nearby_tickets",
    description="Find active tickets near a given lat/lon location.",
    input_schema={
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
            "radius_meters": {"type": "number", "default": 50.0},
        },
        "required": ["latitude", "longitude"],
    },
)
async def find_nearby_tickets_tool(
    latitude: float, longitude: float, radius_meters: float = 50.0, db: AsyncSession = None
) -> Dict[str, Any]:
    service = TicketService(db)
    tickets = await service.find_nearby_tickets(latitude, longitude, radius_meters)
    return {
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "asset_id": t.asset_id,
            }
            for t in tickets
        ]
    }


# Alias searchNearbyTickets to find_nearby_tickets
@tool_registry.register(
    name="search_nearby_tickets",
    description="Locate tickets near given GPS coordinates.",
    input_schema={
        "type": "object",
        "properties": {
            "latitude": {"type": "number"},
            "longitude": {"type": "number"},
            "radius_meters": {"type": "number", "default": 50.0},
        },
        "required": ["latitude", "longitude"],
    },
)
async def search_nearby_tickets_tool(
    latitude: float, longitude: float, radius_meters: float = 50.0, db: AsyncSession = None
) -> Dict[str, Any]:
    return await find_nearby_tickets_tool(latitude, longitude, radius_meters, db)


@tool_registry.register(
    name="update_ticket_status",
    description="Update the status of a specific work ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of ticket to update"},
            "status": {"type": "string", "enum": ["open", "in_progress", "completed", "resolved", "closed"]},
        },
        "required": ["ticket_id", "status"],
    },
    requires_confirmation=True,
)
async def update_ticket_status_tool(
    ticket_id: int, status: str, db: AsyncSession = None
) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.update_ticket(ticket_id, {"status": status})
        return {
            "ticket_id": t.id,
            "status": t.status,
            "message": f"Ticket #{t.id} status updated to {t.status}.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="update_ticket",
    description="Modify details of an existing work ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of ticket to update"},
            "status": {"type": "string", "enum": ["open", "in_progress", "completed", "resolved", "closed"]},
            "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
            "title": {"type": "string"},
            "description": {"type": "string"},
        },
        "required": ["ticket_id"],
    },
    requires_confirmation=True,
)
async def update_ticket_tool(ticket_id: int, db: AsyncSession = None, **kwargs) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.update_ticket(ticket_id, kwargs)
        return {
            "ticket_id": t.id,
            "status": t.status,
            "priority": t.priority,
            "message": f"Ticket #{t.id} updated.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="assign_ticket",
    description="Assign a ticket to a technician.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of ticket"},
            "technician_id": {"type": "integer", "description": "ID of technician to assign"},
        },
        "required": ["ticket_id", "technician_id"],
    },
    requires_confirmation=True,
)
async def assign_ticket_tool(
    ticket_id: int, technician_id: int, db: AsyncSession = None
) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.assign_ticket(ticket_id, technician_id)
        return {
            "ticket_id": t.id,
            "technician_id": t.technician_id,
            "message": f"Ticket #{t.id} assigned to technician #{technician_id}.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="close_ticket",
    description="Close a completed work ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of the ticket to close"}
        },
        "required": ["ticket_id"],
    },
    requires_confirmation=True,
)
async def close_ticket_tool(ticket_id: int, db: AsyncSession = None) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.close_ticket(ticket_id)
        return {"ticket_id": t.id, "status": t.status, "message": f"Ticket #{t.id} closed."}
    except NotFoundException as e:
        return {"error": str(e)}


# --- Service Tools ---

@tool_registry.register(
    name="start_service",
    description="Start work/service on a ticket, marking status as in_progress.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of the ticket to start service on"}
        },
        "required": ["ticket_id"],
    },
)
async def start_service_tool(ticket_id: int, db: AsyncSession = None) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.start_service(ticket_id)
        return {
            "ticket_id": t.id,
            "status": t.status,
            "message": f"Started service on Ticket #{t.id}. Status set to in_progress.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="complete_service",
    description="Finish/complete service on a ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of the ticket to complete"}
        },
        "required": ["ticket_id"],
    },
    requires_confirmation=True,
)
async def complete_service_tool(ticket_id: int, db: AsyncSession = None) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.complete_service(ticket_id)
        return {
            "ticket_id": t.id,
            "status": t.status,
            "message": f"Service on Ticket #{t.id} completed.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="upload_service_images",
    description="Attach service photos/images to a ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of ticket"},
            "image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of uploaded image URLs or file names",
            },
        },
        "required": ["ticket_id", "image_urls"],
    },
)
async def upload_service_images_tool(
    ticket_id: int, image_urls: List[str], db: AsyncSession = None
) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.upload_service_images(ticket_id, image_urls)
        return {
            "ticket_id": t.id,
            "message": f"Uploaded {len(image_urls)} image(s) to Ticket #{t.id}.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="add_service_notes",
    description="Add technician notes to a work ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of ticket"},
            "notes": {"type": "string", "description": "Technician field notes or work details"},
        },
        "required": ["ticket_id", "notes"],
    },
)
async def add_service_notes_tool(
    ticket_id: int, notes: str, db: AsyncSession = None
) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        t = await service.add_service_notes(ticket_id, notes)
        return {
            "ticket_id": t.id,
            "message": f"Added field notes to Ticket #{t.id}.",
        }
    except NotFoundException as e:
        return {"error": str(e)}


@tool_registry.register(
    name="generate_service_summary",
    description="Generate a audio-friendly summary description of a ticket.",
    input_schema={
        "type": "object",
        "properties": {
            "ticket_id": {"type": "integer", "description": "ID of ticket"}
        },
        "required": ["ticket_id"],
    },
)
async def generate_service_summary_tool(
    ticket_id: int, db: AsyncSession = None
) -> Dict[str, Any]:
    service = TicketService(db)
    try:
        summary = await service.summarize_ticket(ticket_id)
        return {"ticket_id": ticket_id, "summary": summary}
    except NotFoundException as e:
        return {"error": str(e)}


# --- Location & Memory Tools ---

@tool_registry.register(
    name="get_location",
    description="Request GPS coordinate tracking from technician environment.",
    input_schema={"type": "object", "properties": {}},
)
async def get_location_tool() -> Dict[str, Any]:
    return {"status": "request_location", "message": "Location requested."}


@tool_registry.register(
    name="save_memory",
    description="Store context into long term semantic technician assistant memory.",
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Text content to save"}
        },
        "required": ["content"],
    },
)
async def save_memory_tool(
    content: str, user_id: int = None, db: AsyncSession = None
) -> Dict[str, Any]:
    memory_service = MemoryService(db)
    mem = await memory_service.save_semantic_memory(user_id, content)
    return {"memory_id": mem.id, "status": "saved"}


@tool_registry.register(
    name="retrieve_memory",
    description="Query semantic database to retrieve similar prior chats or info.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Semantic query string"}
        },
        "required": ["query"],
    },
)
async def retrieve_memory_tool(
    query: str, user_id: int = None, db: AsyncSession = None
) -> Dict[str, Any]:
    memory_service = MemoryService(db)
    mems = await memory_service.search_semantic_memory(user_id, query)
    return {"memories": mems}


@tool_registry.register(
    name="find_nearby_assets_with_open_tickets",
    description="Locate nearby assets within a specified geographic radius that have open/in-progress tickets.",
    input_schema={
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "description": "Latitude coordinate"},
            "longitude": {"type": "number", "description": "Longitude coordinate"},
            "radius_meters": {"type": "number", "description": "Search radius in meters. Default is 1000m."},
        },
        "required": ["latitude", "longitude"],
    },
)
async def find_nearby_assets_with_open_tickets_tool(
    latitude: float, longitude: float, radius_meters: float = 1000.0, db: AsyncSession = None
) -> Dict[str, Any]:
    from app.database.models.asset import Asset
    from app.database.models.ticket import Ticket
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    delta = radius_meters / 111000.0
    result = await db.execute(
        select(Asset)
        .join(Ticket, Asset.id == Ticket.asset_id)
        .filter(
            Asset.latitude.between(latitude - delta, latitude + delta),
            Asset.longitude.between(longitude - delta, longitude + delta),
            Ticket.status.in_(["open", "in_progress"])
        )
        .options(selectinload(Asset.tickets))
        .distinct()
    )
    assets = list(result.scalars().all())
    return {
        "assets": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "sku": a.sku,
                "status": a.status,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "open_tickets": [
                    {
                        "id": t.id,
                        "title": t.title,
                        "status": t.status,
                        "priority": t.priority
                    }
                    for t in a.tickets if t.status in ["open", "in_progress"]
                ]
            }
            for a in assets
        ]
    }


@tool_registry.register(
    name="get_my_recently_completed_tickets",
    description="Retrieve the last 10 completed or closed work tickets that were assigned to the current technician.",
    input_schema={"type": "object", "properties": {}},
)
async def get_my_recently_completed_tickets_tool(
    user_id: int = None, db: AsyncSession = None
) -> Dict[str, Any]:
    from app.database.models.ticket import Ticket
    from sqlalchemy import select, desc
    
    if not user_id:
        return {"tickets": []}

    result = await db.execute(
        select(Ticket)
        .filter(
            Ticket.technician_id == user_id,
            Ticket.status.in_(["completed", "closed"])
        )
        .order_by(desc(Ticket.updated_at))
        .limit(10)
    )
    tickets = list(result.scalars().all())
    return {
        "tickets": [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "asset_id": t.asset_id,
                "completed_at": t.updated_at.isoformat() if t.updated_at else None
            }
            for t in tickets
        ]
    }


# Public exports
ALL_TOOLS = tool_registry.get_schemas()


async def execute_tool(
    name: str, args: Dict[str, Any], user_id: int, db: AsyncSession
) -> Dict[str, Any]:
    return await tool_registry.execute_tool(name, args, user_id, db)
