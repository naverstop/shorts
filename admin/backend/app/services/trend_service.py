"""
Trend Service
- 트렌드 수집 및 분석
- YouTube/TikTok 트렌드 통합
"""
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from loguru import logger

from app.models.trend import Trend
from app.services.youtube_client import YouTubeClient
from app.services.gemini_client import GeminiClient


class TrendService:
    """트렌드 수집 및 분석 서비스"""
    
    def __init__(self):
        self.youtube_client = YouTubeClient()
        self.gemini_client = GeminiClient()
    
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
            # YouTube trending videos 가져오기
            logger.info(f"📊 Collecting YouTube trends for {region_code}")
            videos = await self.youtube_client.get_trending_videos(
                region_code=region_code,
                category_id=category_id,
                max_results=50
            )
            
            if not videos:
                logger.warning("No trending videos found")
                raise ValueError(f"{region_code} 지역의 트렌딩 영상을 찾을 수 없습니다.")
            
            # Gemini로 트렌드 분석
            logger.info("🤖 Analyzing trends with Gemini")
            analysis = await self.gemini_client.analyze_trend(videos, language="ko")
            
            if not analysis:
                logger.warning("Trend analysis failed")
                raise ValueError("Gemini AI 트렌드 분석에 실패했습니다.")
            
            # Trend 저장
            trends = []
            keywords = analysis.get("keywords", [])
            main_topics = analysis.get("main_topics", [])
            
            for keyword in keywords[:10]:  # 상위 10개 키워드만 저장
                # 중복 체크
                result = await db.execute(
                    select(Trend).where(
                        and_(
                            Trend.keyword == keyword,
                            Trend.source == "youtube",
                            Trend.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
                        )
                    )
                )
                existing_trend = result.scalar_one_or_none()
                
                if existing_trend:
                    # 기존 트렌드 업데이트
                    existing_trend.trend_score = analysis.get("viral_potential", 70)
                    existing_trend.ai_analysis = analysis
                    existing_trend.updated_at = datetime.now(timezone.utc)
                    trends.append(existing_trend)
                    logger.info(f"  📝 Updated existing trend: {keyword}")
                else:
                    # 신규 트렌드 생성
                    trend = Trend(
                        source="youtube",
                        keyword=keyword,
                        topic=main_topics[0] if main_topics else None,
                        category=category_id or "general",
                        trend_score=analysis.get("viral_potential", 70),
                        view_count=sum(v.get("view_count", 0) for v in videos[:10]),
                        video_count=len(videos),
                        growth_rate=0.0,
                        ai_analysis=analysis,
                        suggested_tags=[f"#{k}" for k in keywords[:5]],
                        related_keywords=keywords[:10],
                        language="ko",
                        region=region_code,
                        collected_at=datetime.now(timezone.utc),
                        expires_at=datetime.now(timezone.utc) + timedelta(days=14)
                    )
                    db.add(trend)
                    trends.append(trend)
                    logger.info(f"  ✨ Created new trend: {keyword}")
            
            await db.commit()
            logger.info(f"✅ Collected {len(trends)} trends")
            return trends
            
        except ValueError as ve:
            # 명확한 오류 메시지를 가진 경우 그대로 전파
            logger.error(f"❌ {str(ve)}")
            await db.rollback()
            raise
        except Exception as e:
            logger.error(f"❌ Failed to collect YouTube trends: {e}")
            await db.rollback()
            raise ValueError(f"트렌드 수집 중 오류 발생: {str(e)}")
    
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
            
            query = query.order_by(desc(Trend.trend_score)).limit(limit)
            
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
