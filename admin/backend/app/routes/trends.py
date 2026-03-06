"""
Trend API Routes
- 트렌드 수집 및 조회
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import TrendResponse, TrendCollectRequest, TrendSearchRequest, TrendSourceResponse
from app.dependencies import get_current_user
from app.services.trend_service import TrendService
from app.trend_sources import get_enabled_trend_source_codes, get_trend_sources

router = APIRouter(prefix="/api/v1/trends", tags=["Trends"])


@router.get("/sources", response_model=List[TrendSourceResponse])
async def get_available_trend_sources(
    current_user: User = Depends(get_current_user)
):
    return get_trend_sources()


@router.post("/collect", response_model=List[TrendResponse])
async def collect_trends(
    request: TrendCollectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    트렌드 수집
    - YouTube에서 현재 트렌드 수집
    - Gemini AI로 분석
    """
    try:
        service = TrendService()
        enabled_sources = set(get_enabled_trend_source_codes())
        requested_sources = request.sources or list(enabled_sources)
        invalid_sources = [source for source in requested_sources if source not in enabled_sources]

        if invalid_sources:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 트렌드 소스입니다: {', '.join(invalid_sources)}"
            )

        source_collectors = {
            "youtube": lambda: service.collect_youtube_trends(
                db=db,
                region_code=request.region_code,
                category_id=request.category_id,
            ),
            "youtube_shorts": lambda: service.collect_youtube_shorts_trends(
                db=db,
                region_code=request.region_code,
                category_id=request.category_id,
            ),
            "tiktok": lambda: service.collect_tiktok_trends(
                db=db,
                region_code=request.region_code,
            ),
        }

        collected_trends: List[TrendResponse] = []
        errors: list[str] = []

        for source in requested_sources:
            try:
                trends = await source_collectors[source]()
                collected_trends.extend(trends)
            except Exception as exc:
                errors.append(f"{source}: {str(exc)}")

        if not collected_trends:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="트렌드를 수집할 수 없습니다. " + "; ".join(errors)
            )

        return collected_trends
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"트렌드 수집 중 오류 발생: {str(e)}"
        )


@router.get("", response_model=List[TrendResponse])
async def get_trending_keywords(
    source: Optional[str] = None,
    limit: int = 20,
    min_score: float = 50.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    트렌딩 키워드 조회
    - 최근 7일 이내 트렌드
    - 점수 기준 정렬
    """
    service = TrendService()
    trends = await service.get_trending_keywords(
        db=db,
        source=source,
        limit=limit,
        min_score=min_score
    )
    
    return trends


@router.post("/search", response_model=List[TrendResponse])
async def search_trends(
    request: TrendSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    트렌드 검색
    - 키워드/토픽 기반 검색
    """
    service = TrendService()
    trends = await service.search_trends(
        db=db,
        query=request.query,
        source=request.source
    )
    
    return trends


@router.get("/{trend_id}", response_model=TrendResponse)
async def get_trend_detail(
    trend_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """트렌드 상세 조회"""
    from sqlalchemy import select
    from app.models.trend import Trend
    
    result = await db.execute(
        select(Trend).where(Trend.id == trend_id)
    )
    trend = result.scalar_one_or_none()
    
    if not trend:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trend not found"
        )
    
    return trend
