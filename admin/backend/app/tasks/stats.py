"""
Video Statistics Sync Background Tasks

영상 성과 동기화 Celery Tasks
Phase 1.5에서 활성화
"""
from app.celery_app import celery_app
import logging
import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.video import Video

logger = logging.getLogger(__name__)


def _to_decimal(value: Decimal | float | int | None) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _calculate_roi_score(video: Video) -> Decimal:
    """내부 지표 기반 ROI 점수(0~100) 계산"""
    views = max(video.views or 0, 0)
    likes = max(video.likes or 0, 0)
    comments = max(video.comments or 0, 0)
    ctr = max(_to_decimal(video.ctr), Decimal("0"))
    cpm = max(_to_decimal(video.cpm), Decimal("0"))

    engagement_rate = Decimal("0")
    if views > 0:
        engagement_rate = (Decimal(likes + comments) / Decimal(views)) * Decimal("100")

    score = (
        (engagement_rate * Decimal("2.0"))
        + (ctr * Decimal("2.5"))
        + (cpm * Decimal("1.5"))
    )
    return min(score.quantize(Decimal("0.01")), Decimal("100.00"))


async def _sync_video_stats_async() -> dict:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Video))
        videos = result.scalars().all()

        synced_count = 0
        now = datetime.now(timezone.utc)

        for video in videos:
            avg_view_duration = 0
            if (video.views or 0) > 0:
                avg_view_duration = int((video.watch_time or 0) / max(video.views, 1))

            video.avg_view_duration = avg_view_duration
            video.roi_score = _calculate_roi_score(video)
            video.last_synced_at = now
            synced_count += 1

        await db.commit()

        return {
            "status": "completed",
            "videos_synced": synced_count,
            "synced_at": now.isoformat(),
        }


async def _analyze_video_performance_async() -> dict:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Video))
        videos = result.scalars().all()

        analyzed_count = len(videos)
        if analyzed_count == 0:
            return {
                "status": "completed",
                "videos_analyzed": 0,
                "top_video_id": None,
                "avg_roi_score": "0.00",
            }

        roi_scores = [_to_decimal(video.roi_score) for video in videos]
        total_roi = sum(roi_scores, Decimal("0"))
        avg_roi = (total_roi / Decimal(analyzed_count)).quantize(Decimal("0.01"))

        top_video = max(videos, key=lambda v: _to_decimal(v.roi_score))

        return {
            "status": "completed",
            "videos_analyzed": analyzed_count,
            "top_video_id": top_video.id,
            "avg_roi_score": str(avg_roi),
        }


@celery_app.task(name="app.tasks.stats.sync_video_stats")
def sync_video_stats():
    """
    플랫폼 API에서 영상 성과 데이터 동기화
    
    - 내부 성과 지표 재계산
    - videos 테이블의 avg_view_duration, roi_score, last_synced_at 업데이트
    """
    try:
        logger.info("📊 Sync video stats task started")
        return asyncio.run(_sync_video_stats_async())

    except Exception as e:
        logger.error(f"❌ Sync video stats failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.stats.analyze_video_performance")
def analyze_video_performance():
    """
    영상 성과 분석 및 AI 피드백 생성
    
    - 업로드된 영상 ROI 평균 계산
    - 상위 성과 영상 식별
    """
    try:
        logger.info("🔍 Analyze video performance task started")
        return asyncio.run(_analyze_video_performance_async())

    except Exception as e:
        logger.error(f"❌ Analyze video performance failed: {e}")
        return {"status": "error", "message": str(e)}
