"""
Tests for trends Celery tasks
"""
from types import SimpleNamespace

from app.tasks import trends as trends_tasks


class _DummySession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


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


def test_collect_youtube_trends_task_success(monkeypatch):
    class _DummyTrendService:
        async def collect_youtube_trends(self, db, region_code, category_id):
            assert region_code == "KR"
            assert category_id == "10"
            return [
                SimpleNamespace(keyword="ai"),
                SimpleNamespace(keyword="shorts"),
            ]

    monkeypatch.setattr(trends_tasks, "AsyncSessionLocal", lambda: _DummySession())
    monkeypatch.setattr(trends_tasks, "TrendService", _DummyTrendService)

    result = trends_tasks.collect_youtube_trends.run(region_code="KR", category_id="10")

    assert result["status"] == "completed"
    assert result["source"] == "youtube"
    assert result["trends_collected"] == 2
    assert result["keywords"] == ["ai", "shorts"]


def test_collect_youtube_trends_task_error(monkeypatch):
    class _ErrorTrendService:
        async def collect_youtube_trends(self, db, region_code, category_id):
            raise RuntimeError("boom")

    monkeypatch.setattr(trends_tasks, "AsyncSessionLocal", lambda: _DummySession())
    monkeypatch.setattr(trends_tasks, "TrendService", _ErrorTrendService)

    result = trends_tasks.collect_youtube_trends.run(region_code="US", category_id=None)

    assert result["status"] == "error"
    assert result["source"] == "youtube"
    assert result["region_code"] == "US"
    assert "boom" in result["message"]


def test_collect_tiktok_trends_task_success(monkeypatch):
    class _TikTokDb:
        def __init__(self):
            self.call = 0
            self.added = []
            self.committed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def execute(self, _query):
            self.call += 1
            if self.call == 1:
                return _ResultList([
                    SimpleNamespace(
                        keyword="ai",
                        trend_score=80.0,
                        topic="tech",
                        category="general",
                        view_count=1000,
                        video_count=120,
                        growth_rate=12.5,
                        related_keywords=["ai", "automation"],
                        suggested_tags=["#ai", "#tech"],
                        language="ko",
                    ),
                    SimpleNamespace(
                        keyword="shorts",
                        trend_score=75.0,
                        topic="content",
                        category="general",
                        view_count=800,
                        video_count=90,
                        growth_rate=10.1,
                        related_keywords=["shorts"],
                        suggested_tags=["#shorts"],
                        language="ko",
                    ),
                ])
            return _ResultList([])

        def add(self, obj):
            self.added.append(obj)

        async def commit(self):
            self.committed = True

    db = _TikTokDb()
    monkeypatch.setattr(trends_tasks, "AsyncSessionLocal", lambda: db)

    result = trends_tasks.collect_tiktok_trends.run(region_code="KR")

    assert result["status"] == "completed"
    assert result["source"] == "tiktok"
    assert result["trends_collected"] == 2
    assert set(result["keywords"]) == {"ai", "shorts"}
    assert db.committed is True
    assert len(db.added) == 2


def test_collect_tiktok_trends_task_error(monkeypatch):
    async def _raise_async(region_code: str):
        raise RuntimeError("tiktok-boom")

    monkeypatch.setattr(trends_tasks, "_collect_tiktok_trends_async", _raise_async)

    result = trends_tasks.collect_tiktok_trends.run(region_code="US")

    assert result["status"] == "error"
    assert result["source"] == "tiktok"
    assert result["region_code"] == "US"
    assert "tiktok-boom" in result["message"]
