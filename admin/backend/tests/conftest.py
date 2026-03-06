"""
Test configuration and fixtures
"""
import os
import pytest
from fastapi.testclient import TestClient
from app.database import AsyncSessionLocal

os.environ.setdefault("APP_ENV", "testing")

from app.main import app


@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)


@pytest.fixture
async def test_db():
    """Async database session fixture (shared test DB)"""
    async with AsyncSessionLocal() as session:
        yield session
