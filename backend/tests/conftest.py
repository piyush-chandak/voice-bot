import asyncio
from typing import Any, AsyncGenerator, Generator
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database.models.base import Base
from app.database.session import get_db
from app.integrations.redis import redis_client

# Use SQLite in-memory for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Mock Redis during tests
class MockRedis:
    def __init__(self):
        self.store = {}

    def connect(self):
        pass

    async def disconnect(self):
        pass

    @property
    def client(self):
        return self

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex=None):
        self.store[key] = value
        return True

    async def delete(self, key: str):
        self.store.pop(key, None)
        return True

    async def get_json(self, key: str):
        import json
        data = self.store.get(key)
        return json.loads(data) if data else None

    async def set_json(self, key: str, value: Any, ex=None):
        import json
        self.store[key] = json.dumps(value)
        return True



@pytest_asyncio.fixture(autouse=True, scope="session")
async def mock_redis_connection():
    mock = MockRedis()
    # Patch the redis_client instance
    redis_client._client = mock
    redis_client.connect = lambda: None
    redis_client.disconnect = lambda: None
    redis_client.get = mock.get
    redis_client.set = mock.set
    redis_client.delete = mock.delete
    redis_client.get_json = mock.get_json
    redis_client.set_json = mock.set_json
    yield mock


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override database dependency injection
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True, scope="session")
def mock_llm_services():
    from app.integrations.anthropic import anthropic_service
    from app.integrations.gemini import gemini_service

    async def mock_generate_message(messages, system_prompt, tools=None, temperature=0.0):
        last_user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "").lower()
                break

        if messages and messages[-1].get("role") == "tool":
            tool_content = messages[-1].get("content", "")
            return {
                "content": f"Here is the tool response content details: {tool_content}",
                "tool_calls": [],
                "usage": {"input_tokens": 5, "output_tokens": 5}
            }

        tool_calls = []
        if "ticket" in last_user_message:
            tool_calls = [{
                "id": "call_mock_ticket",
                "name": "find_nearby_tickets" if "near" in last_user_message else "list_tickets",
                "args": {"latitude": 37.7749, "longitude": -122.4194} if "near" in last_user_message else {"skip": 0, "limit": 10}
            }]
        elif "asset" in last_user_message:
            tool_calls = [{
                "id": "call_mock_asset",
                "name": "find_assets" if "near" in last_user_message else "list_assets",
                "args": {"latitude": 37.7749, "longitude": -122.4194} if "near" in last_user_message else {"skip": 0, "limit": 10}
            }]

        return {
            "content": "Executing requested action...",
            "tool_calls": tool_calls,
            "usage": {"input_tokens": 10, "output_tokens": 15}
        }

    anthropic_service.generate_message = mock_generate_message
    gemini_service.generate_message = mock_generate_message

