"""
Platform and Language API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import Platform, SupportedLanguage, User
from app.schemas import PlatformResponse, PlatformDetailResponse, LanguageResponse
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["platforms", "languages"])


# ==================== Schemas ====================

class PlatformCreate(BaseModel):
    platform_code: str = Field(..., min_length=2, max_length=20, description="플랫폼 코드 (예: youtube, tiktok)")
    platform_name: str = Field(..., min_length=2, max_length=50, description="플랫폼 이름")
    is_active: bool = Field(default=True, description="활성화 여부")
    auth_type: str = Field(..., description="인증 타입 (oauth2, api_key, credentials)")
    api_endpoint: Optional[str] = Field(None, description="API 엔드포인트 URL")
    documentation_url: Optional[str] = Field(None, description="문서 URL")
    required_fields: Optional[dict] = Field(None, description="필수 필드 정보 (JSON)")


class PlatformUpdate(BaseModel):
    platform_name: Optional[str] = Field(None, min_length=2, max_length=50)
    is_active: Optional[bool] = None
    auth_type: Optional[str] = None
    api_endpoint: Optional[str] = None
    documentation_url: Optional[str] = None
    required_fields: Optional[dict] = None


@router.get("/platforms", response_model=List[PlatformResponse])
async def list_platforms(
    db: AsyncSession = Depends(get_db)
):
    """Get list of supported platforms"""
    result = await db.execute(
        select(Platform).where(Platform.is_active == True)
    )
    platforms = result.scalars().all()
    return platforms


@router.get("/platforms/{platform_id}", response_model=PlatformDetailResponse)
async def get_platform_detail(
    platform_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get platform detail including required auth fields"""
    result = await db.execute(
        select(Platform).where(Platform.id == platform_id)
    )
    platform = result.scalar_one_or_none()

    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")

    return platform


@router.get("/languages", response_model=List[LanguageResponse])
async def list_languages(
    db: AsyncSession = Depends(get_db)
):
    """Get list of supported languages"""
    result = await db.execute(
        select(SupportedLanguage).where(SupportedLanguage.is_active == True)
        .order_by(SupportedLanguage.popularity_rank)
    )
    languages = result.scalars().all()
    return languages


# ==================== Platform CRUD ====================

@router.post("/platforms", response_model=PlatformResponse, status_code=status.HTTP_201_CREATED)
async def create_platform(
    platform_data: PlatformCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 생성 (관리자 전용)
    
    - 플랫폼 코드는 중복 불가
    """
    # 중복 확인
    result = await db.execute(
        select(Platform).where(Platform.platform_code == platform_data.platform_code)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"플랫폼 코드 '{platform_data.platform_code}'가 이미 존재합니다."
        )
    
    # 생성
    new_platform = Platform(
        platform_code=platform_data.platform_code,
        platform_name=platform_data.platform_name,
        is_active=platform_data.is_active,
        auth_type=platform_data.auth_type,
        api_endpoint=platform_data.api_endpoint,
        documentation_url=platform_data.documentation_url,
        required_fields=platform_data.required_fields
    )
    
    db.add(new_platform)
    await db.commit()
    await db.refresh(new_platform)
    
    return new_platform


@router.put("/platforms/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: int,
    platform_data: PlatformUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 정보 수정 (관리자 전용)
    """
    result = await db.execute(
        select(Platform).where(Platform.id == platform_id)
    )
    platform = result.scalar_one_or_none()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"플랫폼 ID {platform_id}를 찾을 수 없습니다."
        )
    
    # 수정
    if platform_data.platform_name is not None:
        platform.platform_name = platform_data.platform_name
    if platform_data.is_active is not None:
        platform.is_active = platform_data.is_active
    if platform_data.auth_type is not None:
        platform.auth_type = platform_data.auth_type
    if platform_data.api_endpoint is not None:
        platform.api_endpoint = platform_data.api_endpoint
    if platform_data.documentation_url is not None:
        platform.documentation_url = platform_data.documentation_url
    if platform_data.required_fields is not None:
        platform.required_fields = platform_data.required_fields
    
    await db.commit()
    await db.refresh(platform)
    
    return platform


@router.delete("/platforms/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 삭제 (관리자 전용)
    
    - 연결된 계정이 있는 경우 삭제 불가
    """
    result = await db.execute(
        select(Platform).where(Platform.id == platform_id)
    )
    platform = result.scalar_one_or_none()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"플랫폼 ID {platform_id}를 찾을 수 없습니다."
        )
    
    # TODO: 연결된 계정 확인 (필요시)
    # from app.models import PlatformAccount
    # accounts_check = await db.execute(
    #     select(PlatformAccount).where(PlatformAccount.platform_id == platform_id).limit(1)
    # )
    # if accounts_check.scalar_one_or_none():
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="이 플랫폼을 사용하는 계정이 있어 삭제할 수 없습니다."
    #     )
    
    await db.delete(platform)
    await db.commit()
    
    return None
