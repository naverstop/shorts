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
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        now = datetime.now(timezone.utc)

        # 0) TikTok Discover 실수집 시도
        collected_keywords: list[str] = []
        try:
            tiktok_client = TikTokTrendClient()
            collected_keywords = await tiktok_client.fetch_discover_keywords(region_code=region_code, limit=20)
        except Exception:
            collected_keywords = []

        if collected_keywords:
            existing_result = await db.execute(
                select(Trend).where(
                    and_(
                        Trend.source == "tiktok",
                        Trend.region == region_code,
                        Trend.created_at >= cutoff,
                    )
                )
            )
            existing_tiktok = {trend.keyword: trend for trend in existing_result.scalars().all()}

            collected = []
            for index, keyword in enumerate(collected_keywords[:20]):
                score = max(100.0 - (index * 2.5), 55.0)
                if keyword in existing_tiktok:
                    trend = existing_tiktok[keyword]
                    trend.trend_score = score
                    trend.topic = trend.topic or "discover"
                    trend.category = trend.category or "general"
                    trend.ai_analysis = {
                        "source": "tiktok_discover_scrape",
                        "collected_at": now.isoformat(),
                    }
                    trend.related_keywords = collected_keywords[:10]
                    trend.suggested_tags = [f"#{k}" for k in collected_keywords[:5]]
                    trend.language = trend.language or "ko"
                    trend.collected_at = now
                    trend.expires_at = now + timedelta(days=7)
                    trend.updated_at = now
                    collected.append(trend)
                else:
                    trend = Trend(
                        source="tiktok",
                        keyword=keyword,
                        topic="discover",
                        category="general",
                        trend_score=score,
                        view_count=0,
                        video_count=0,
                        growth_rate=0.0,
                        ai_analysis={
                            "source": "tiktok_discover_scrape",
                            "collected_at": now.isoformat(),
                        },
                        suggested_tags=[f"#{k}" for k in collected_keywords[:5]],
                        related_keywords=collected_keywords[:10],
                        language="ko",
                        region=region_code,
                        collected_at=now,
                        expires_at=now + timedelta(days=7),
                    )
                    db.add(trend)
                    collected.append(trend)

            await db.commit()

            return {
                "status": "completed",
                "source": "tiktok",
                "region_code": region_code,
                "collection_mode": "tiktok_discover_scrape",
                "trends_collected": len(collected),
                "keywords": [trend.keyword for trend in collected[:10]],
            }

        # 1) 최근 YouTube 상위 트렌드 조회
        youtube_result = await db.execute(
            select(Trend)
            .where(
                and_(
                    Trend.source == "youtube",
                    Trend.region == region_code,
                    Trend.created_at >= cutoff,
                )
            )
            .order_by(desc(Trend.trend_score))
            .limit(10)
        )
        youtube_trends = youtube_result.scalars().all()

        # 데이터가 없으면 기본 키워드로 초기화
        if not youtube_trends:
            youtube_trends = [
                Trend(keyword="shorts", trend_score=70.0, topic="general", category="general", language="ko", source="youtube", collected_at=datetime.now(timezone.utc)),
                Trend(keyword="viral", trend_score=68.0, topic="general", category="general", language="ko", source="youtube", collected_at=datetime.now(timezone.utc)),
                Trend(keyword="challenge", trend_score=66.0, topic="general", category="general", language="ko", source="youtube", collected_at=datetime.now(timezone.utc)),
            ]

        # 2) 기존 TikTok 트렌드 조회 (중복/업데이트 처리)
        existing_result = await db.execute(
            select(Trend).where(
                and_(
                    Trend.source == "tiktok",
                    Trend.region == region_code,
                    Trend.created_at >= cutoff,
                )
            )
        )
        existing_tiktok = {
            trend.keyword: trend
            for trend in existing_result.scalars().all()
        }

        collected = []

        for source_trend in youtube_trends[:10]:
            keyword = source_trend.keyword
            base_score = float(source_trend.trend_score or 60.0)
            tiktok_score = min(base_score * 1.08, 100.0)

            if keyword in existing_tiktok:
                trend = existing_tiktok[keyword]
                trend.trend_score = tiktok_score
                trend.topic = source_trend.topic
                trend.category = source_trend.category or "general"
                trend.view_count = source_trend.view_count or 0
                trend.video_count = source_trend.video_count or 0
                trend.growth_rate = source_trend.growth_rate or 0.0
                trend.ai_analysis = {
                    "derived_from": "youtube",
                    "sync_type": "cross_platform_projection",
                    "synced_at": now.isoformat(),
                }
                trend.related_keywords = source_trend.related_keywords
                trend.suggested_tags = source_trend.suggested_tags
                trend.language = source_trend.language or "ko"
                trend.collected_at = now
                trend.expires_at = now + timedelta(days=7)
                trend.updated_at = now
                collected.append(trend)
            else:
                trend = Trend(
                    source="tiktok",
                    keyword=keyword,
                    topic=source_trend.topic,
                    category=source_trend.category or "general",
                    trend_score=tiktok_score,
                    view_count=source_trend.view_count or 0,
                    video_count=source_trend.video_count or 0,
                    growth_rate=source_trend.growth_rate or 0.0,
                    ai_analysis={
                        "derived_from": "youtube",
                        "sync_type": "cross_platform_projection",
                        "synced_at": now.isoformat(),
                    },
                    suggested_tags=source_trend.suggested_tags,
                    related_keywords=source_trend.related_keywords,
                    language=source_trend.language or "ko",
                    region=region_code,
                    collected_at=now,
                    expires_at=now + timedelta(days=7),
                )
                db.add(trend)
                collected.append(trend)

        await db.commit()

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
