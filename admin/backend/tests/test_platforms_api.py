"""
Platform API tests
"""
from types import SimpleNamespace

from app.database import get_db
from app.main import app


class _ScalarList:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


class _ResultList:
    def __init__(self, items):
        self._items = items

    def scalars(self):
        return _ScalarList(self._items)


class _ResultOne:
    def __init__(self, item):
        self._item = item

    def scalar_one_or_none(self):
        return self._item


class _FakeListDb:
    async def execute(self, _query):
        return _ResultList([
            SimpleNamespace(
                id=1,
                platform_code="youtube",
                platform_name="YouTube",
                is_active=True,
                auth_type="oauth2",
                api_endpoint="https://www.googleapis.com",
            )
        ])


class _FakeDetailDb:
    async def execute(self, _query):
        return _ResultOne(
            SimpleNamespace(
                id=1,
                platform_code="youtube",
                platform_name="YouTube",
                is_active=True,
                auth_type="oauth2",
                api_endpoint="https://www.googleapis.com",
                required_fields={"client_id": "string", "client_secret": "string"},
                documentation_url="https://developers.google.com/youtube",
            )
        )


class _FakeMissingDb:
    async def execute(self, _query):
        return _ResultOne(None)


def test_list_platforms_with_override(client):
    async def override_get_db():
        yield _FakeListDb()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/platforms")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["platform_code"] == "youtube"
    finally:
        app.dependency_overrides.clear()


def test_get_platform_detail_with_required_fields(client):
    async def override_get_db():
        yield _FakeDetailDb()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/platforms/1")
        assert response.status_code == 200
        data = response.json()
        assert data["platform_code"] == "youtube"
        assert "required_fields" in data
        assert data["required_fields"]["client_id"] == "string"
    finally:
        app.dependency_overrides.clear()


def test_get_platform_detail_not_found(client):
    async def override_get_db():
        yield _FakeMissingDb()

    app.dependency_overrides[get_db] = override_get_db
    try:
        response = client.get("/api/v1/platforms/999")
        assert response.status_code == 404
        assert response.json()["error"] == "Platform not found"
    finally:
        app.dependency_overrides.clear()
