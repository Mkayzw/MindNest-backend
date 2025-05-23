# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from typing import Generator

from app.main import app # Assuming your FastAPI app instance is here
from app.database import Base, engine # For test database setup

# If you plan to use a separate test database:
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from app.core.config import settings # If your DB URL is in settings

# TEST_DATABASE_URL = settings.DATABASE_URL + "_test" # Example: append _test
# engine_test = create_engine(TEST_DATABASE_URL)
# SessionLocal_test = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function") # Or "session" if DB setup is per session
async def test_db():
    # This is a placeholder. For a real test DB:
    # Base.metadata.create_all(bind=engine_test) # Create tables in test DB
    # yield SessionLocal_test # Provide a session
    # Base.metadata.drop_all(bind=engine_test) # Drop tables after tests
    # For now, we'll just yield None as we don't have a separate test DB configured yet
    yield None


from httpx import ASGITransport

@pytest.fixture(scope="function")
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://127.0.0.1:8000") as ac: # Adjust base_url if needed
        yield ac
