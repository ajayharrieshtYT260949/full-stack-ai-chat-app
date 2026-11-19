import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.models import Base
from app.main import create_app
from app.database import get_db
from app.config import get_settings

@pytest_asyncio.fixture
async def test_client(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async def override_db():
        async with factory() as session:
            yield session
    app = create_app()
    app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(get_settings(), "chat_api_key", "test-secret")
    monkeypatch.setattr(get_settings(), "rate_limit_messages", 20)
    monkeypatch.setattr(get_settings(), "rate_limit_window_seconds", 3600)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, factory
    await engine.dispose()
