"""
Script API Routes
- AI 스크립트 생성 및 관리
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.script import Script
from app.schemas import (
    ScriptGenerateRequest,
    ScriptResponse,
    ScriptSimilarityResponse
)
from app.dependencies import get_current_user
from app.services.script_service import ScriptService

router = APIRouter(prefix="/api/v1/scripts", tags=["Scripts"])


@router.post("", response_model=ScriptResponse, status_code=status.HTTP_201_CREATED)
async def generate_script(
    request: ScriptGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI 스크립트 생성
    - Claude AI로 Hook-Body-CTA 구조 스크립트 생성
    - OpenAI Embedding으로 Vector 저장
    """
    service = ScriptService()
    script = await service.generate_script(
        db=db,
        user_id=current_user.id,
        topic=request.topic,
        trend_id=request.trend_id,
        target_audience=request.target_audience,
        platform=request.platform,
        language=request.language,
        duration=request.duration
    )
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate script"
        )
    
    return script


@router.get("", response_model=List[ScriptResponse])
async def get_my_scripts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """내 스크립트 목록 조회"""
    service = ScriptService()
    scripts = await service.get_user_scripts(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return scripts


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script_detail(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """스크립트 상세 조회"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Script).where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    # 본인 스크립트만 조회 가능
    if script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this script"
        )
    
    return script


@router.get("/{script_id}/similar", response_model=List[ScriptSimilarityResponse])
async def find_similar_scripts(
    script_id: int,
    similarity_threshold: float = Query(0.85, ge=0.0, le=1.0),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    유사 스크립트 검색
    - Vector 유사도 기반 검색
    - 중복 콘텐츠 방지
    """
    # 스크립트 소유권 확인
    from sqlalchemy import select
    
    result = await db.execute(
        select(Script).where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this script"
        )
    
    # 유사 스크립트 검색
    service = ScriptService()
    similar_scripts = await service.find_similar_scripts(
        db=db,
        script_id=script_id,
        similarity_threshold=similarity_threshold,
        limit=limit
    )
    
    return similar_scripts


@router.delete("/{script_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_script(
    script_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """스크립트 삭제"""
    from sqlalchemy import select
    
    result = await db.execute(
        select(Script).where(Script.id == script_id)
    )
    script = result.scalar_one_or_none()
    
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Script not found"
        )
    
    if script.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this script"
        )
    
    await db.delete(script)
    await db.commit()
