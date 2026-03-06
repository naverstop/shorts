"""
Trend API Routes
- 트렌드 수집 및 조회
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.schemas import TrendResponse, TrendCollectRequest, TrendSearchRequest
from app.dependencies import get_current_user
from app.services.trend_service import TrendService

router = APIRouter(prefix="/api/v1/trends", tags=["Trends"])


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
    service = TrendService()
    trends = await service.collect_youtube_trends(
        db=db,
        region_code=request.region_code,
        category_id=request.category_id
    )
    
    if not trends:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to collect trends"
        )
    
    return trends


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
