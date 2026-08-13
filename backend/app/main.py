from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.middleware import RequestLoggingMiddleware
from app.integrations.redis import redis_client

# Include Routers
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.location import router as location_router
from app.api.v1.asset import router as asset_router
from app.api.v1.ticket import router as ticket_router
from app.api.v1.memory import router as memory_router
from app.api.v1.chat import router as chat_router
from app.api.v1.voice import router as voice_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize logging and Redis
    setup_logging(settings.LOG_LEVEL)
    logger.info("Initializing Voice Technician Assistant application startup...")
    redis_client.connect()

    # Automatically initialize schemas if running on SQLite
    if settings.DATABASE_URL and "sqlite" in settings.DATABASE_URL:
        from app.database.models.base import Base
        from app.database.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Local SQLite database initialized successfully.")

    yield
    # Shutdown: Close Redis
    await redis_client.disconnect()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
origins = [
    "*",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request tracking middleware
app.add_middleware(RequestLoggingMiddleware)

# Include API Routers
app.include_router(health_router, prefix=f"{settings.API_V1_STR}/health")
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth")
app.include_router(location_router, prefix=f"{settings.API_V1_STR}/location")
app.include_router(asset_router, prefix=f"{settings.API_V1_STR}/assets")
app.include_router(ticket_router, prefix=f"{settings.API_V1_STR}/tickets")
app.include_router(memory_router, prefix=f"{settings.API_V1_STR}/memory")
app.include_router(chat_router, prefix=f"{settings.API_V1_STR}/chat")
app.include_router(voice_router, prefix=f"{settings.API_V1_STR}/voice")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AI Voice Technician Assistant API",
        version="1.0.0",
        description=(
            "Production-ready backend for voice-enabled field technicians. "
            "Supports coordinates logging, asset proximity checks, ticket CRUD, "
            "semantic memory storage, and real-time chat/voice streaming."
        ),
        routes=app.routes,
    )

    # Configure JWT Security Scheme in Swagger
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Input your JWT token to access endpoints.",
        }
    }

    # Apply JWT security globally to all endpoints except auth and health
    for path, path_data in openapi_schema["paths"].items():
        if "auth" in path or "health" in path:
            continue
        for method in path_data:
            path_data[method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
