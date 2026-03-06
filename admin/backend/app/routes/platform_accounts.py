"""
Platform Account Routes (v2.0 Architecture)
플랫폼 계정 관리 API (SIM 기반)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models import PlatformAccount, PlatformAccountStats, SimCard, Platform, User, UploadQuota, Agent
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/platform-accounts", tags=["Platform Accounts"])


# ==================== Helper Functions ====================

def extract_channels_from_account(account: PlatformAccount) -> tuple[List[dict], int]:
    """
    PlatformAccount에서 채널 정보 추출
    sim_card → agent → channels 경로로 접근
    """
    channels = []
    try:
        if account.sim_card and account.sim_card.agent and account.sim_card.agent.channels:
            channels = [
                {
                    "id": ch.id,
                    "channel_id": ch.channel_id,
                    "channel_name": ch.channel_name,
                    "platform": ch.platform,
                    "status": ch.status,
                    "created_at": ch.created_at.isoformat() if ch.created_at else None
                }
                for ch in account.sim_card.agent.channels
            ]
    except Exception:
        pass
    
    return channels, len(channels)


# ==================== Schemas ====================

class PlatformAccountCreate(BaseModel):
    """플랫폼 계정 생성 요청"""
    sim_id: int = Field(..., description="SIM 카드 ID (필수)")
    platform_id: int = Field(..., description="플랫폼 ID (1=YouTube, 2=TikTok)")
    account_name: str = Field(..., min_length=1, max_length=100, description="계정 이름")
    account_identifier: Optional[str] = Field(None, max_length=200, description="계정 식별자 (채널 ID 등)")
    credentials: Dict[str, Any] = Field(..., description="인증 정보 (JSON)")
    is_primary: bool = Field(False, description="기본 계정 여부")
    notes: Optional[str] = None


class PlatformAccountUpdate(BaseModel):
    """플랫폼 계정 수정 요청"""
    account_name: Optional[str] = None
    account_identifier: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, pattern="^(active|banned|expired|inactive)$")
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class PlatformAccountResponse(BaseModel):
    """플랫폼 계정 응답"""
    id: int
    user_id: int
    sim_id: int
    platform_id: int
    account_name: str
    account_identifier: Optional[str]
    status: str
    last_validated: Optional[datetime]
    last_used: Optional[datetime]
    ban_detected_at: Optional[datetime]
    ban_reason: Optional[str]
    is_primary: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # 계산 필드
    display_name: str
    is_active: bool
    is_banned: bool
    has_quota: bool
    
    # 채널 정보
    channels: List[dict] = Field(default_factory=list, description="이 계정으로 운영되는 채널 목록")
    channel_count: int = Field(0, description="운영 채널 수")
    
    class Config:
        from_attributes = True


class PlatformAccountDetailResponse(PlatformAccountResponse):
    """플랫폼 계정 상세 응답 (통계 및 할당량 포함)"""
    sim_info: Optional[dict] = None
    platform_info: Optional[dict] = None
    stats: Optional[dict] = None
    quota: Optional[dict] = None


# ==================== Routes ====================

@router.post("/", response_model=PlatformAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_platform_account(
    account_data: PlatformAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 계정 등록
    
    - SIM 카드에 플랫폼 계정 연결
    - 동일 SIM + 플랫폼 + 계정명 조합은 중복 불가
    - 통계 테이블 자동 생성
    """
    # SIM 소유권 확인
    result = await db.execute(
        select(SimCard).where(
            SimCard.id == account_data.sim_id,
            SimCard.user_id == current_user.id
        )
    )
    sim = result.scalar_one_or_none()
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM ID {account_data.sim_id}를 찾을 수 없습니다."
        )
    
    # 플랫폼 확인
    result = await db.execute(
        select(Platform).where(Platform.id == account_data.platform_id)
    )
    platform = result.scalar_one_or_none()
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"플랫폼 ID {account_data.platform_id}를 찾을 수 없습니다."
        )
    
    # 중복 확인 (SIM + 플랫폼 + 계정명)
    result = await db.execute(
        select(PlatformAccount).where(
            and_(
                PlatformAccount.sim_id == account_data.sim_id,
                PlatformAccount.platform_id == account_data.platform_id,
                PlatformAccount.account_name == account_data.account_name
            )
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SIM '{sim.sim_number}'에 '{platform.platform_name}' 계정 '{account_data.account_name}'이(가) 이미 등록되어 있습니다."
        )
    
    # 계정 생성
    new_account = PlatformAccount(
        user_id=current_user.id,
        sim_id=account_data.sim_id,
        platform_id=account_data.platform_id,
        account_name=account_data.account_name,
        account_identifier=account_data.account_identifier,
        credentials=account_data.credentials,  # TODO: 암호화 필요
        is_primary=account_data.is_primary,
        notes=account_data.notes,
        status="active"
    )
    
    db.add(new_account)
    await db.flush()  # ID 생성
    
    # 통계 테이블 생성
    stats = PlatformAccountStats(
        platform_account_id=new_account.id
    )
    db.add(stats)
    
    await db.commit()
    await db.refresh(new_account)
    
    # selectinload로 관계 로드 (lazy loading 방지)
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == new_account.id)
        .options(
            selectinload(PlatformAccount.platform),
            selectinload(PlatformAccount.sim_card).selectinload(SimCard.agent).selectinload(Agent.channels),
            selectinload(PlatformAccount.upload_quota)
        )
    )
    new_account = result.scalar_one()
    
    return PlatformAccountResponse(
        id=new_account.id,
        user_id=new_account.user_id,
        sim_id=new_account.sim_id,
        platform_id=new_account.platform_id,
        account_name=new_account.account_name,
        account_identifier=new_account.account_identifier,
        status=new_account.status,
        last_validated=new_account.last_validated,
        last_used=new_account.last_used,
        ban_detected_at=new_account.ban_detected_at,
        ban_reason=new_account.ban_reason,
        is_primary=new_account.is_primary,
        notes=new_account.notes,
        created_at=new_account.created_at,
        updated_at=new_account.updated_at,
        display_name=new_account.display_name,
        is_active=new_account.is_active,
        is_banned=new_account.is_banned,
        has_quota=new_account.has_quota
    )


@router.get("/", response_model=List[PlatformAccountResponse])
async def list_platform_accounts(
    sim_id: Optional[int] = None,
    platform_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 계정 목록 조회
    
    - SIM, 플랫폼, 상태별 필터링 가능
    """
    query = select(PlatformAccount).where(PlatformAccount.user_id == current_user.id).options(
        selectinload(PlatformAccount.sim_card).selectinload(SimCard.agent).selectinload(Agent.channels),
        selectinload(PlatformAccount.platform),
        selectinload(PlatformAccount.upload_quota)
    )
    
    if sim_id:
        query = query.where(PlatformAccount.sim_id == sim_id)
    if platform_id:
        query = query.where(PlatformAccount.platform_id == platform_id)
    if status_filter:
        query = query.where(PlatformAccount.status == status_filter)
    
    query = query.offset(skip).limit(limit).order_by(PlatformAccount.created_at.desc())
    
    result = await db.execute(query)
    accounts = result.scalars().all()
    
    return [
        PlatformAccountResponse(
            id=acc.id,
            user_id=acc.user_id,
            sim_id=acc.sim_id,
            platform_id=acc.platform_id,
            account_name=acc.account_name,
            account_identifier=acc.account_identifier,
            status=acc.status,
            last_validated=acc.last_validated,
            last_used=acc.last_used,
            ban_detected_at=acc.ban_detected_at,
            ban_reason=acc.ban_reason,
            is_primary=acc.is_primary,
            notes=acc.notes,
            created_at=acc.created_at,
            updated_at=acc.updated_at,
            display_name=acc.display_name,
            is_active=acc.is_active,
            is_banned=acc.is_banned,
            has_quota=acc.has_quota
        )
        for acc in accounts
    ]


@router.get("/{account_id}", response_model=PlatformAccountDetailResponse)
async def get_platform_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 계정 상세 조회
    
    - SIM 정보 포함
    - 통계 정보 포함
    - 할당량 정보 포함
    """
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id, PlatformAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"계정 ID {account_id}를 찾을 수 없습니다."
        )
    
    # SIM 정보
    sim_info = {
        "id": account.sim_card.id,
        "sim_number": account.sim_card.sim_number,
        "carrier": account.sim_card.carrier,
        "status": account.sim_card.status
    } if account.sim_card else None
    
    # 플랫폼 정보
    platform_info = {
        "id": account.platform.id,
        "platform_code": account.platform.platform_code,
        "platform_name": account.platform.platform_name
    } if account.platform else None
    
    # 통계 정보
    stats_info = None
    if account.stats:
        stats_info = {
            "total_uploads": account.stats.total_uploads,
            "successful_uploads": account.stats.successful_uploads,
            "failed_uploads": account.stats.failed_uploads,
            "success_rate": account.stats.success_rate,
            "consecutive_failures": account.stats.consecutive_failures,
            "last_upload_at": account.stats.last_upload_at
        }
    
    # 할당량 정보
    quota_info = None
    if account.upload_quota:
        quota = account.upload_quota
        quota_info = {
            "id": quota.id,
            "daily_limit": quota.daily_limit,
            "weekly_limit": quota.weekly_limit,
            "monthly_limit": quota.monthly_limit,
            "used_today": quota.used_today,
            "used_week": quota.used_week,
            "used_month": quota.used_month,
            "remaining_daily": quota.get_remaining_daily(),
            "remaining_weekly": quota.get_remaining_weekly(),
            "remaining_monthly": quota.get_remaining_monthly(),
            "is_exceeded": quota.is_quota_exceeded()
        }
    
    return PlatformAccountDetailResponse(
        id=account.id,
        user_id=account.user_id,
        sim_id=account.sim_id,
        platform_id=account.platform_id,
        account_name=account.account_name,
        account_identifier=account.account_identifier,
        status=account.status,
        last_validated=account.last_validated,
        last_used=account.last_used,
        ban_detected_at=account.ban_detected_at,
        ban_reason=account.ban_reason,
        is_primary=account.is_primary,
        notes=account.notes,
        created_at=account.created_at,
        updated_at=account.updated_at,
        display_name=account.display_name,
        is_active=account.is_active,
        is_banned=account.is_banned,
        has_quota=account.has_quota,
        sim_info=sim_info,
        platform_info=platform_info,
        stats=stats_info,
        quota=quota_info
    )


@router.put("/{account_id}", response_model=PlatformAccountResponse)
async def update_platform_account(
    account_id: int,
    account_data: PlatformAccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 계정 수정
    
    - 계정 이름, 인증 정보, 상태 등 수정 가능
    """
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id, PlatformAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"계정 ID {account_id}를 찾을 수 없습니다."
        )
    
    # 수정
    update_data = account_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)
    
    await db.commit()
    await db.refresh(account)
    
    return PlatformAccountResponse(
        id=account.id,
        user_id=account.user_id,
        sim_id=account.sim_id,
        platform_id=account.platform_id,
        account_name=account.account_name,
        account_identifier=account.account_identifier,
        status=account.status,
        last_validated=account.last_validated,
        last_used=account.last_used,
        ban_detected_at=account.ban_detected_at,
        ban_reason=account.ban_reason,
        is_primary=account.is_primary,
        notes=account.notes,
        created_at=account.created_at,
        updated_at=account.updated_at,
        display_name=account.display_name,
        is_active=account.is_active,
        is_banned=account.is_banned,
        has_quota=account.has_quota
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 계정 삭제
    
    - 할당량 및 통계도 함께 삭제됨 (cascade)
    """
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id, PlatformAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"계정 ID {account_id}를 찾을 수 없습니다."
        )
    
    await db.delete(account)
    await db.commit()


@router.post("/{account_id}/ban")
async def mark_account_as_banned(
    account_id: int,
    reason: str = "Manual ban",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    계정 차단 처리
    """
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id, PlatformAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"계정 ID {account_id}를 찾을 수 없습니다."
        )
    
    account.mark_as_banned(reason)
    await db.commit()
    
    return {"message": f"계정 '{account.account_name}'이(가) 차단되었습니다.", "reason": reason}


@router.post("/{account_id}/activate")
async def activate_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    계정 활성화
    """
    result = await db.execute(
        select(PlatformAccount)
        .where(PlatformAccount.id == account_id, PlatformAccount.user_id == current_user.id)
    )
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"계정 ID {account_id}를 찾을 수 없습니다."
        )
    
    account.mark_as_active()
    await db.commit()
    
    return {"message": f"계정 '{account.account_name}'이(가) 활성화되었습니다."}


@router.post("/validate-credentials")
async def validate_platform_credentials(
    platform_id: int,
    credentials: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    플랫폼 인증 정보 검증
    
    - JSON 구조 확인
    - 필수 필드 확인
    - 실제 API 연동 테스트 (가능한 경우)
    """
    # 플랫폼 조회
    result = await db.execute(
        select(Platform).where(Platform.id == platform_id)
    )
    platform = result.scalar_one_or_none()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="플랫폼을 찾을 수 없습니다."
        )
    
    errors = []
    warnings = []
    
    # 1. 필수 필드 확인 (플랫폼별)
    required_fields_map = {
        "youtube": ["client_id", "client_secret"],
        "tiktok": ["app_id", "app_secret"],
        "instagram": ["app_id", "app_secret"],
        "facebook": ["app_id", "app_secret"],
    }
    
    required_fields = required_fields_map.get(platform.platform_code, [])
    
    for field in required_fields:
        if field not in credentials:
            errors.append(f"필수 필드 '{field}'가 누락되었습니다.")
        elif not credentials[field] or not str(credentials[field]).strip():
            errors.append(f"필수 필드 '{field}'의 값이 비어있습니다.")
    
    # 2. 데이터 타입 확인
    for key, value in credentials.items():
        if value is None:
            warnings.append(f"필드 '{key}'의 값이 null입니다.")
        elif isinstance(value, str) and len(value) > 500:
            warnings.append(f"필드 '{key}'의 길이가 너무 깁니다 ({len(value)}자).")
    
    # 3. 플랫폼별 특정 검증
    if platform.platform_code == "youtube":
        if "client_id" in credentials:
            client_id = str(credentials["client_id"])
            if not client_id.endswith(".apps.googleusercontent.com"):
                warnings.append("YouTube Client ID 형식이 올바르지 않을 수 있습니다 (*.apps.googleusercontent.com).")
        
        if "client_secret" in credentials:
            secret = str(credentials["client_secret"])
            if not secret.startswith("GOCSPX-") and len(secret) < 20:
                warnings.append("YouTube Client Secret 형식이 의심스럽습니다.")
    
    elif platform.platform_code == "tiktok":
        if "app_id" in credentials:
            app_id = str(credentials["app_id"])
            if not app_id.isdigit() or len(app_id) < 10:
                warnings.append("TikTok App ID는 10자리 이상의 숫자여야 합니다.")
    
    # 4. API 키 길이 확인
    if "api_key" in credentials:
        api_key = str(credentials["api_key"])
        if len(api_key) < 20:
            warnings.append("API Key가 너무 짧습니다. 올바른 키인지 확인하세요.")
    
    # 결과 반환
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "platform_code": platform.platform_code,
        "platform_name": platform.platform_name,
        "errors": errors,
        "warnings": warnings,
        "message": "검증 성공" if is_valid else "검증 실패",
        "checked_fields": list(credentials.keys()),
        "missing_fields": [f for f in required_fields if f not in credentials]
    }

