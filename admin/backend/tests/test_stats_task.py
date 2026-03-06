"""
Tests for stats Celery tasks
"""
from decimal import Decimal
from types import SimpleNamespace

from app.tasks import stats as stats_tasks


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


class _DummyDb:
    def __init__(self, videos):
        self._videos = videos
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, _query):
        return _ResultList(self._videos)

    async def commit(self):
        self.committed = True


def test_sync_video_stats_success(monkeypatch):
    videos = [
        SimpleNamespace(
            id=1,
            views=100,
            likes=12,
            comments=4,
            watch_time=500,
            ctr=Decimal("3.5"),
            cpm=Decimal("1.2"),
            avg_view_duration=0,
            roi_score=Decimal("0"),
            last_synced_at=None,
        )
    ]

    db = _DummyDb(videos)
    monkeypatch.setattr(stats_tasks, "AsyncSessionLocal", lambda: db)

    result = stats_tasks.sync_video_stats.run()

    assert result["status"] == "completed"
    assert result["videos_synced"] == 1
    assert videos[0].avg_view_duration == 5
    assert videos[0].last_synced_at is not None
    assert db.committed is True


def test_analyze_video_performance_success(monkeypatch):
    videos = [
        SimpleNamespace(id=1, roi_score=Decimal("12.50")),
        SimpleNamespace(id=2, roi_score=Decimal("20.00")),
        SimpleNamespace(id=3, roi_score=Decimal("7.50")),
    ]

    db = _DummyDb(videos)
    monkeypatch.setattr(stats_tasks, "AsyncSessionLocal", lambda: db)

    result = stats_tasks.analyze_video_performance.run()

    assert result["status"] == "completed"
    assert result["videos_analyzed"] == 3
    assert result["top_video_id"] == 2
    assert result["avg_roi_score"] == "13.33"


def test_analyze_video_performance_empty(monkeypatch):
    db = _DummyDb([])
    monkeypatch.setattr(stats_tasks, "AsyncSessionLocal", lambda: db)

    result = stats_tasks.analyze_video_performance.run()

    assert result["status"] == "completed"
    assert result["videos_analyzed"] == 0
    assert result["top_video_id"] is None
    assert result["avg_roi_score"] == "0.00"
