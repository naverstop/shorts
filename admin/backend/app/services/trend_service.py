"""
Trend Service
- 트렌드 수집 및 분석
- YouTube/TikTok 트렌드 통합
"""
import re

from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from loguru import logger

from app.models.trend import Trend
from app.services.youtube_client import YouTubeClient
from app.services.gemini_client import GeminiClient
from app.services.tiktok_trend_client import TikTokTrendClient


class TrendService:
    """트렌드 수집 및 분석 서비스"""
    
    def __init__(self):
        self.youtube_client = YouTubeClient()
        self.gemini_client = GeminiClient()
        self.tiktok_client = TikTokTrendClient()

    def _normalize_keyword(self, value: str) -> str:
        return re.sub(r"\s+", "", (value or "").strip().lower())

    def _calculate_keyword_metrics(self, keyword: str, videos: List[Dict]) -> tuple[int, int]:
        """키워드와 제목/태그가 매칭되는 영상들의 조회수 합계와 개수 계산"""
        normalized_keyword = self._normalize_keyword(keyword)
        matched_videos: List[Dict] = []

        for video in videos:
            haystacks = [
                self._normalize_keyword(str(video.get("title", ""))),
                self._normalize_keyword(str(video.get("description", ""))),
            ]
            haystacks.extend(
                self._normalize_keyword(str(tag)) for tag in (video.get("tags", []) or [])
            )

            if any(normalized_keyword and normalized_keyword in haystack for haystack in haystacks):
                matched_videos.append(video)

        if matched_videos:
            return (
                sum(video.get("view_count", 0) for video in matched_videos),
                len(matched_videos),
            )

        # 직접 매칭이 없으면 상위 10개 평균 조회수를 기준값으로 사용
        top_videos = videos[:10]
        average_views = int(
            sum(video.get("view_count", 0) for video in top_videos) / max(len(top_videos), 1)
        )
        return average_views, 0

    def _calculate_growth_rate(self, previous_view_count: int, current_view_count: int) -> float:
        """이전 조회수 대비 성장률 계산"""
        if previous_view_count <= 0:
            return 0.0

        return round(((current_view_count - previous_view_count) / previous_view_count) * 100, 1)

    def _parse_duration_seconds(self, duration: str | None) -> int:
        if not duration:
            return 0

        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return (hours * 3600) + (minutes * 60) + seconds

    async def _collect_keyword_trends(
        self,
        db: AsyncSession,
        source: str,
        videos: List[Dict],
        region_code: str,
        category_id: Optional[str] = None,
        language: str = "ko",
    ) -> List[Trend]:
        if not videos:
            return []

        logger.info(f"🤖 Analyzing trends with Gemini for source={source}")
        analysis = await self.gemini_client.analyze_trend(videos, language=language)

        if not analysis:
            logger.warning("Trend analysis failed")
            raise ValueError("Gemini AI 트렌드 분석에 실패했습니다.")

        trends = []
        keywords = analysis.get("keywords", [])
        main_topics = analysis.get("main_topics", [])

        for keyword in keywords[:10]:
            keyword_view_count, keyword_video_count = self._calculate_keyword_metrics(keyword, videos)

            result = await db.execute(
                select(Trend).where(
                    and_(
                        Trend.keyword == keyword,
                        Trend.source == source,
                        Trend.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
                    )
                )
            )
            existing_trend = result.scalar_one_or_none()

            if existing_trend:
                previous_view_count = int(existing_trend.view_count or 0)
                existing_trend.topic = main_topics[0] if main_topics else existing_trend.topic
                existing_trend.category = category_id or existing_trend.category or "general"
                existing_trend.trend_score = analysis.get("viral_potential", 70)
                existing_trend.view_count = keyword_view_count
                existing_trend.video_count = keyword_video_count
                existing_trend.growth_rate = self._calculate_growth_rate(previous_view_count, keyword_view_count)
                existing_trend.related_keywords = keywords[:10]
                existing_trend.suggested_tags = [f"#{k}" for k in keywords[:5]]
                existing_trend.ai_analysis = analysis
                existing_trend.region = region_code
                existing_trend.language = language
                existing_trend.collected_at = datetime.now(timezone.utc)
                existing_trend.expires_at = datetime.now(timezone.utc) + timedelta(days=14)
                existing_trend.updated_at = datetime.now(timezone.utc)
                trends.append(existing_trend)
                logger.info(f"  📝 Updated existing trend [{source}]: {keyword}")
            else:
                trend = Trend(
                    source=source,
                    keyword=keyword,
                    topic=main_topics[0] if main_topics else None,
                    category=category_id or "general",
                    trend_score=analysis.get("viral_potential", 70),
                    view_count=keyword_view_count,
                    video_count=keyword_video_count,
                    growth_rate=0.0,
                    ai_analysis=analysis,
                    suggested_tags=[f"#{k}" for k in keywords[:5]],
                    related_keywords=keywords[:10],
                    language=language,
                    region=region_code,
                    collected_at=datetime.now(timezone.utc),
                    expires_at=datetime.now(timezone.utc) + timedelta(days=14)
                )
                db.add(trend)
                trends.append(trend)
                logger.info(f"  ✨ Created new trend [{source}]: {keyword}")

        await db.commit()
        logger.info(f"✅ Collected {len(trends)} trends for source={source}")
        return trends
    
    async def collect_youtube_trends(
        self,
        db: AsyncSession,
        region_code: str = "KR",
        category_id: Optional[str] = None
    ) -> List[Trend]:
        """
        YouTube 트렌드 수집
        
        Args:
            db: Database session
            region_code: 지역 코드
            category_id: 카테고리 ID
        
        Returns:
            생성된 Trend 리스트
        """
        try:
            logger.info(f"📊 Collecting YouTube trends for {region_code}")
            videos = await self.youtube_client.get_trending_videos(
                region_code=region_code,
                category_id=category_id,
                max_results=50
            )
            
            if not videos:
                logger.warning("No trending videos found")
                raise ValueError(f"{region_code} 지역의 트렌딩 영상을 찾을 수 없습니다.")
            return await self._collect_keyword_trends(
                db=db,
                source="youtube",
                videos=videos,
                region_code=region_code,
                category_id=category_id,
            )
            
        except ValueError as ve:
            # 명확한 오류 메시지를 가진 경우 그대로 전파
            logger.error(f"❌ {str(ve)}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"❌ Failed to collect YouTube trends: {e}")
            await db.rollback()
            raise ValueError(f"트렌드 수집 중 오류 발생: {str(e)}")

    async def collect_youtube_shorts_trends(
        self,
        db: AsyncSession,
        region_code: str = "KR",
        category_id: Optional[str] = None
    ) -> List[Trend]:
        """YouTube 트렌딩 중 Shorts 후보(60초 이하) 수집"""
        try:
            logger.info(f"📊 Collecting YouTube Shorts trends for {region_code}")
            videos = await self.youtube_client.get_trending_videos(
                region_code=region_code,
                category_id=category_id,
                max_results=50
            )

            short_videos = [
                video for video in videos
                if self._parse_duration_seconds(str(video.get("duration", ""))) <= 60
            ]

            if not short_videos:
                logger.warning("No YouTube Shorts candidates found")
                raise ValueError(f"{region_code} 지역의 Shorts 후보 영상을 찾을 수 없습니다.")

            return await self._collect_keyword_trends(
                db=db,
                source="youtube_shorts",
                videos=short_videos,
                region_code=region_code,
                category_id=category_id,
            )

        except ValueError as ve:
            logger.error(f"❌ {str(ve)}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"❌ Failed to collect YouTube Shorts trends: {e}")
            await db.rollback()
            raise ValueError(f"YouTube Shorts 트렌드 수집 중 오류 발생: {str(e)}")

    async def collect_tiktok_trends(
        self,
        db: AsyncSession,
        region_code: str = "KR"
    ) -> List[Trend]:
        """TikTok Discover 실수집 우선, 실패 시 YouTube Shorts/YouTube 기반 fallback"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        now = datetime.now(timezone.utc)

        collected_keywords: list[str] = []
        try:
            collected_keywords = await self.tiktok_client.fetch_discover_keywords(region_code=region_code, limit=20)
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

            collected: List[Trend] = []
            for index, keyword in enumerate(collected_keywords[:20]):
                score = max(100.0 - (index * 2.5), 55.0)
                if keyword in existing_tiktok:
                    trend = existing_tiktok[keyword]
                    previous_view_count = int(trend.view_count or 0)
                    trend.trend_score = score
                    trend.topic = trend.topic or "discover"
                    trend.category = trend.category or "general"
                    trend.growth_rate = self._calculate_growth_rate(previous_view_count, int(trend.view_count or 0))
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
            return collected

        youtube_result = await db.execute(
            select(Trend)
            .where(
                and_(
                    Trend.source.in_(["youtube_shorts", "youtube"]),
                    Trend.region == region_code,
                    Trend.created_at >= cutoff,
                )
            )
            .order_by(desc(Trend.collected_at), desc(Trend.trend_score))
            .limit(10)
        )
        seed_trends = youtube_result.scalars().all()

        if not seed_trends:
            raise ValueError("TikTok 트렌드 생성을 위한 기반 데이터가 없습니다.")

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

        collected: List[Trend] = []

        for source_trend in seed_trends[:10]:
            keyword = source_trend.keyword
            base_score = float(source_trend.trend_score or 60.0)
            tiktok_score = min(base_score * 1.08, 100.0)

            if keyword in existing_tiktok:
                trend = existing_tiktok[keyword]
                previous_view_count = int(trend.view_count or 0)
                current_view_count = int(source_trend.view_count or 0)
                trend.trend_score = tiktok_score
                trend.topic = source_trend.topic
                trend.category = source_trend.category or "general"
                trend.view_count = current_view_count
                trend.video_count = source_trend.video_count or 0
                trend.growth_rate = self._calculate_growth_rate(previous_view_count, current_view_count)
                trend.ai_analysis = {
                    "derived_from": source_trend.source,
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
                    growth_rate=0.0,
                    ai_analysis={
                        "derived_from": source_trend.source,
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
        return collected
    
    async def get_trending_keywords(
        self,
        db: AsyncSession,
        source: Optional[str] = None,
        limit: int = 20,
        min_score: float = 50.0
    ) -> List[Trend]:
        """
        트렌딩 키워드 조회
        
        Args:
            db: Database session
            source: 소스 필터 (youtube, tiktok, etc)
            limit: 최대 결과 수
            min_score: 최소 트렌드 점수
        
        Returns:
            Trend 리스트
        """
        try:
            query = select(Trend).where(
                and_(
                    Trend.trend_score >= min_score,
                    Trend.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
                )
            )
            
            if source:
                query = query.where(Trend.source == source)
            
            query = query.order_by(desc(Trend.collected_at), desc(Trend.trend_score)).limit(limit)
            
            result = await db.execute(query)
            trends = result.scalars().all()
            
            logger.info(f"📊 Found {len(trends)} trending keywords")
            return list(trends)
            
        except Exception as e:
            logger.error(f"❌ Failed to get trending keywords: {e}")
            return []
    
    async def search_trends(
        self,
        db: AsyncSession,
        query: str,
        source: Optional[str] = None
    ) -> List[Trend]:
        """
        트렌드 검색
        
        Args:
            db: Database session
            query: 검색 쿼리
            source: 소스 필터
        
        Returns:
            Trend 리스트
        """
        try:
            stmt = select(Trend).where(
                or_(
                    Trend.keyword.ilike(f"%{query}%"),
                    Trend.topic.ilike(f"%{query}%")
                )
            )
            
            if source:
                stmt = stmt.where(Trend.source == source)
            
            stmt = stmt.order_by(desc(Trend.trend_score)).limit(20)
            
            result = await db.execute(stmt)
            trends = result.scalars().all()
            
            logger.info(f"🔍 Found {len(trends)} trends for query: {query}")
            return list(trends)
            
        except Exception as e:
            logger.error(f"❌ Failed to search trends: {e}")
            return []
