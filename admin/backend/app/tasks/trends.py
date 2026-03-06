"""
Trends Collection Background Tasks

플랫폼 트렌드 수집 및 분석 Celery Tasks
Phase 1.5에서 활성화
"""
from app.celery_app import celery_app
import logging
import asyncio
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, and_, desc

from app.database import AsyncSessionLocal
from app.models.trend import Trend
from app.services.trend_service import TrendService
from app.services.tiktok_trend_client import TikTokTrendClient

logger = logging.getLogger(__name__)


async def _collect_youtube_trends_async(region_code: str = "KR", category_id: str | None = None) -> dict:
    """YouTube 트렌드 수집 비동기 실행 함수"""
    async with AsyncSessionLocal() as db:
        service = TrendService()
        trends = await service.collect_youtube_trends(
            db=db,
            region_code=region_code,
            category_id=category_id,
        )

        keywords = [trend.keyword for trend in trends[:10]] if trends else []
        return {
            "status": "completed",
            "source": "youtube",
            "region_code": region_code,
            "category_id": category_id,
            "trends_collected": len(trends),
            "keywords": keywords,
        }


async def _collect_tiktok_trends_async(region_code: str = "KR") -> dict:
    """TikTok Discover 실수집 우선, 실패 시 YouTube 기반 추정 fallback"""
    async with AsyncSessionLocal() as db:
        service = TrendService()
        collected = await service.collect_tiktok_trends(db=db, region_code=region_code)

        return {
            "status": "completed",
            "source": "tiktok",
            "region_code": region_code,
            "trends_collected": len(collected),
            "keywords": [trend.keyword for trend in collected[:10]],
        }


@celery_app.task(name="app.tasks.trends.collect_youtube_trends")
def collect_youtube_trends(region_code: str = "KR", category_id: str | None = None):
    """
    YouTube 트렌드 수집 및 Gemini 분석

    - YouTube Data API로 인기 동영상 조회
    - Gemini API로 트렌드 분석
    - PostgreSQL trends 테이블 저장/업데이트
    """
    try:
        logger.info(
            "📈 Collect YouTube trends task started (region=%s, category=%s)",
            region_code,
            category_id,
        )
        return asyncio.run(_collect_youtube_trends_async(region_code=region_code, category_id=category_id))

    except Exception as e:
        logger.error(f"❌ Collect YouTube trends failed: {e}")
        return {
            "status": "error",
            "source": "youtube",
            "region_code": region_code,
            "category_id": category_id,
            "message": str(e),
        }


@celery_app.task(name="app.tasks.trends.collect_tiktok_trends")
def collect_tiktok_trends(region_code: str = "KR"):
    """
    TikTok 트렌드 수집(내부 크로스플랫폼 추정 기반)

    - 최근 YouTube 트렌드 상위 키워드를 참고하여 TikTok 트렌드 후보 생성
    - 기존 TikTok 트렌드가 있으면 업데이트, 없으면 신규 생성
    """
    try:
        logger.info("📈 Collect TikTok trends task started (region=%s)", region_code)
        return asyncio.run(_collect_tiktok_trends_async(region_code=region_code))

    except Exception as e:
        logger.error(f"❌ Collect TikTok trends failed: {e}")
        return {
            "status": "error",
            "source": "tiktok",
            "region_code": region_code,
            "message": str(e),
        }
