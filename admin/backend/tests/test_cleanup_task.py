"""
Tests for cleanup Celery tasks
"""
from datetime import datetime, timedelta
from types import SimpleNamespace

from app.tasks import cleanup as cleanup_tasks


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


class _DummyCleanupDb:
    def __init__(self, jobs=None, agents=None):
        self.jobs = jobs or []
        self.agents = agents or []
        self.call = 0
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, _query):
        self.call += 1
        if self.jobs and self.call == 1:
            return _ResultList(self.jobs)
        return _ResultList(self.agents)

    async def commit(self):
        self.committed = True


def test_archive_old_jobs_marks_metadata(monkeypatch):
    old_job = SimpleNamespace(id=101, job_metadata={"foo": "bar"})
    already_archived = SimpleNamespace(id=102, job_metadata={"archived": True})

    db = _DummyCleanupDb(jobs=[old_job, already_archived])
    monkeypatch.setattr(cleanup_tasks, "AsyncSessionLocal", lambda: db)

    result = cleanup_tasks.archive_old_jobs.run()

    assert result["status"] == "completed"
    assert result["archived_count"] == 1
    assert 101 in result["archived_job_ids"]
    assert old_job.job_metadata["archived"] is True
    assert db.committed is True


def test_check_agent_disk_usage_threshold(monkeypatch):
    agents = [
        SimpleNamespace(id=1, device_name="A1", disk_usage_percent=45),
        SimpleNamespace(id=2, device_name="A2", disk_usage_percent=80),
        SimpleNamespace(id=3, device_name="A3", disk_usage_percent=92),
    ]

    db = _DummyCleanupDb(agents=agents)
    monkeypatch.setattr(cleanup_tasks, "AsyncSessionLocal", lambda: db)

    result = cleanup_tasks.check_agent_disk_usage.run()

    assert result["status"] == "completed"
    assert result["agents_checked"] == 3
    assert result["cleanup_needed"] == 2
    assert {a["agent_id"] for a in result["agents"]} == {2, 3}
