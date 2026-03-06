"""
SIM Card Routes (v2.0 Architecture)
SIM 카드 관리 API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models import SimCard, Agent, PlatformAccount, User, Platform, UploadQuota
from app.routes.auth import get_current_user

router = APIRouter(prefix="/api/v1/sims", tags=["SIM Cards"])


# ==================== Helper Functions ====================

def extract_platform_accounts_from_sim(sim: SimCard) -> List[dict]:
    """
    SIM 카드에서 플랫폼 계정 정보 추출 (credential 제외)
    """
    accounts = []
    try:
        if sim.platform_accounts:
            for acc in sim.platform_accounts:
                account_data = {
                    "id": acc.id,
                    "platform_id": acc.platform_id,
                    "platform_name": acc.platform.platform_name if acc.platform else None,
                    "account_name": acc.account_name,
                    "account_identifier": acc.account_identifier,
                    "status": acc.status,
                    "is_primary": acc.is_primary,
                    "last_validated": acc.last_validated.isoformat() if acc.last_validated else None,
                    "created_at": acc.created_at.isoformat() if acc.created_at else None
                }
                accounts.append(account_data)
    except Exception:
        pass
    
    return accounts


# ==================== Schemas ====================

class SimCardCreate(BaseModel):
    """SIM 카드 생성 요청"""
    sim_number: str = Field(..., min_length=10, max_length=20, description="SIM 번호 (010-1234-5678)")
    carrier: Optional[str] = Field(None, max_length=50, description="통신사 (SKT, KT, LGU+)")
    google_email: Optional[str] = Field(None, max_length=100, description="연결된 Google 계정")
    nickname: Optional[str] = Field(None, max_length=100, description="별칭")
    notes: Optional[str] = Field(None, description="메모")


class SimCardUpdate(BaseModel):
    """SIM 카드 수정 요청"""
    carrier: Optional[str] = None
    google_email: Optional[str] = None
    google_account_status: Optional[str] = Field(None, pattern="^(active|banned|suspended)$")
    nickname: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(active|inactive|banned)$")


class SimCardResponse(BaseModel):
    """SIM 카드 응답"""
    id: int
    user_id: int
    sim_number: str
    carrier: Optional[str]
    google_email: Optional[str]
    google_account_status: str
    nickname: Optional[str]
    notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    
    # 계산 필드
    display_name: str
    agent_status: str
    total_accounts: int
    
    # 플랫폼 계정 정보
    platform_accounts: List[dict] = Field(default_factory=list, description="등록된 플랫폼 계정 목록")
    
    class Config:
        from_attributes = True


class SimCardDetailResponse(SimCardResponse):
    """SIM 카드 상세 응답 (Agent 및 계정 정보 포함)"""
    agent: Optional[dict] = None
    platform_accounts: List[dict] = []


# ==================== Routes ====================

@router.post("/", response_model=SimCardResponse, status_code=status.HTTP_201_CREATED)
async def create_sim_card(
    sim_data: SimCardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SIM 카드 등록
    
    - 사용자는 SIM 번호와 기본 정보만 입력
    - SIM 번호 중복 체크
    - Google 이메일 중복 체크
    """
    # SIM 번호 중복 확인
    result = await db.execute(
        select(SimCard).where(SimCard.sim_number == sim_data.sim_number)
    )
    existing_sim = result.scalar_one_or_none()
    if existing_sim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SIM 번호 '{sim_data.sim_number}'이(가) 이미 등록되어 있습니다."
        )
    
    # Google 이메일 중복 확인 (입력된 경우)
    if sim_data.google_email:
        result = await db.execute(
            select(SimCard).where(SimCard.google_email == sim_data.google_email)
        )
        existing_email = result.scalar_one_or_none()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google 계정 '{sim_data.google_email}'이(가) 이미 등록되어 있습니다."
            )
    
    # SIM 카드 생성
    new_sim = SimCard(
        user_id=current_user.id,
        sim_number=sim_data.sim_number,
        carrier=sim_data.carrier,
        google_email=sim_data.google_email,
        nickname=sim_data.nickname,
        notes=sim_data.notes,
        status="active",
        google_account_status="active"
    )
    
    db.add(new_sim)
    await db.commit()
    await db.refresh(new_sim)
    
    # selectinload로 관계 로드 (lazy loading 방지)
    result = await db.execute(
        select(SimCard)
        .where(SimCard.id == new_sim.id)
        .options(
            selectinload(SimCard.agent),
            selectinload(SimCard.platform_accounts).selectinload(PlatformAccount.platform)
        )
    )
    new_sim = result.scalar_one()
    
    return SimCardResponse(
        id=new_sim.id,
        user_id=new_sim.user_id,
        sim_number=new_sim.sim_number,
        carrier=new_sim.carrier,
        google_email=new_sim.google_email,
        google_account_status=new_sim.google_account_status,
        nickname=new_sim.nickname,
        notes=new_sim.notes,
        status=new_sim.status,
        created_at=new_sim.created_at,
        updated_at=new_sim.updated_at,
        display_name=new_sim.display_name,
        agent_status=new_sim.agent_status,
        total_accounts=new_sim.total_accounts,
        platform_accounts=extract_platform_accounts_from_sim(new_sim)
    )


@router.get("/", response_model=List[SimCardResponse])
async def list_sim_cards(
    status_filter: Optional[str] = None,
    carrier_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SIM 카드 목록 조회
    
    - 사용자의 SIM 카드 목록 반환
    - status, carrier 필터링 가능
    """
    query = select(SimCard).where(SimCard.user_id == current_user.id).options(
        selectinload(SimCard.agent),
        selectinload(SimCard.platform_accounts).selectinload(PlatformAccount.platform)
    )
    
    if status_filter:
        query = query.where(SimCard.status == status_filter)
    if carrier_filter:
        query = query.where(SimCard.carrier == carrier_filter)
    
    query = query.offset(skip).limit(limit).order_by(SimCard.created_at.desc())
    
    result = await db.execute(query)
    sims = result.scalars().all()
    
    return [
        SimCardResponse(
            id=sim.id,
            user_id=sim.user_id,
            sim_number=sim.sim_number,
            carrier=sim.carrier,
            google_email=sim.google_email,
            google_account_status=sim.google_account_status,
            nickname=sim.nickname,
            notes=sim.notes,
            status=sim.status,
            created_at=sim.created_at,
            updated_at=sim.updated_at,
            display_name=sim.display_name,
            agent_status=sim.agent_status,
            total_accounts=sim.total_accounts,
            platform_accounts=extract_platform_accounts_from_sim(sim)
        )
        for sim in sims
    ]


@router.get("/{sim_id}", response_model=SimCardDetailResponse)
async def get_sim_card(
    sim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SIM 카드 상세 조회
    
    - Agent 정보 포함
    - 등록된 플랫폼 계정 목록 포함
    """
    result = await db.execute(
        select(SimCard)
        .where(SimCard.id == sim_id, SimCard.user_id == current_user.id)
        .options(
            selectinload(SimCard.agent),
            selectinload(SimCard.platform_accounts).selectinload(PlatformAccount.platform)
        )
    )
    sim = result.scalar_one_or_none()
    
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM ID {sim_id}를 찾을 수 없습니다."
        )
    
    # Agent 정보
    agent_data = None
    if sim.agent:
        agent_data = {
            "id": sim.agent.id,
            "device_name": sim.agent.device_name,
            "device_id": sim.agent.device_id,
            "status": sim.agent.status,
            "last_heartbeat": sim.agent.last_heartbeat,
            "android_version": sim.agent.android_version,
            "apk_version": sim.agent.apk_version
        }
    
    # 플랫폼 계정 정보
    accounts_data = [
        {
            "id": acc.id,
            "platform_id": acc.platform_id,
            "platform_name": acc.platform.platform_name if acc.platform else None,
            "account_name": acc.account_name,
            "account_identifier": acc.account_identifier,
            "status": acc.status,
            "is_primary": acc.is_primary,
            "last_validated": acc.last_validated.isoformat() if acc.last_validated else None,
            "created_at": acc.created_at.isoformat() if acc.created_at else None
        }
        for acc in sim.platform_accounts
    ] if sim.platform_accounts else []
    
    return SimCardDetailResponse(
        id=sim.id,
        user_id=sim.user_id,
        sim_number=sim.sim_number,
        carrier=sim.carrier,
        google_email=sim.google_email,
        google_account_status=sim.google_account_status,
        nickname=sim.nickname,
        notes=sim.notes,
        status=sim.status,
        created_at=sim.created_at,
        updated_at=sim.updated_at,
        display_name=sim.display_name,
        agent_status=sim.agent_status,
        total_accounts=sim.total_accounts,
        agent=agent_data,
        platform_accounts=accounts_data
    )


@router.put("/{sim_id}", response_model=SimCardResponse)
async def update_sim_card(
    sim_id: int,
    sim_data: SimCardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SIM 카드 정보 수정
    
    - 별칭, 통신사, Google 계정 등 수정 가능
    - SIM 번호는 수정 불가 (삭제 후 재등록 필요)
    """
    result = await db.execute(
        select(SimCard)
        .where(SimCard.id == sim_id, SimCard.user_id == current_user.id)
    )
    sim = result.scalar_one_or_none()
    
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM ID {sim_id}를 찾을 수 없습니다."
        )
    
    # Google 이메일 중복 확인
    if sim_data.google_email and sim_data.google_email != sim.google_email:
        result = await db.execute(
            select(SimCard).where(SimCard.google_email == sim_data.google_email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Google 계정 '{sim_data.google_email}'이(가) 이미 등록되어 있습니다."
            )
    
    # 수정
    update_data = sim_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sim, key, value)
    
    await db.commit()
    await db.refresh(sim)
    
    # selectinload로 관계 로드 (lazy loading 방지)
    result = await db.execute(
        select(SimCard)
        .where(SimCard.id == sim.id)
        .options(
            selectinload(SimCard.agent),
            selectinload(SimCard.platform_accounts).selectinload(PlatformAccount.platform)
        )
    )
    sim = result.scalar_one()
    
    return SimCardResponse(
        id=sim.id,
        user_id=sim.user_id,
        sim_number=sim.sim_number,
        carrier=sim.carrier,
        google_email=sim.google_email,
        google_account_status=sim.google_account_status,
        nickname=sim.nickname,
        notes=sim.notes,
        status=sim.status,
        created_at=sim.created_at,
        updated_at=sim.updated_at,
        display_name=sim.display_name,
        agent_status=sim.agent_status,
        total_accounts=sim.total_accounts,
        platform_accounts=extract_platform_accounts_from_sim(sim)
    )


@router.delete("/{sim_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sim_card(
    sim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SIM 카드 삭제
    
    - Agent와 플랫폼 계정도 함께 삭제됨 (cascade)
    - 주의: 복구 불가능
    """
    result = await db.execute(
        select(SimCard)
        .where(SimCard.id == sim_id, SimCard.user_id == current_user.id)
    )
    sim = result.scalar_one_or_none()
    
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM ID {sim_id}를 찾을 수 없습니다."
        )
    
    await db.delete(sim)
    await db.commit()


@router.get("/{sim_id}/stats")
async def get_sim_stats(
    sim_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    SIM 카드 통계
    
    - 등록된 플랫폼 계정 수
    - 처리한 Job 수
    - Agent 온라인 상태
    """
    result = await db.execute(
        select(SimCard)
        .where(SimCard.id == sim_id, SimCard.user_id == current_user.id)
    )
    sim = result.scalar_one_or_none()
    
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SIM ID {sim_id}를 찾을 수 없습니다."
        )
    
    # Job 통계
    from app.models import Job
    result = await db.execute(
        select(func.count(Job.id))
        .where(Job.target_sim_id == sim_id)
    )
    total_jobs = result.scalar() or 0
    
    result = await db.execute(
        select(func.count(Job.id))
        .where(Job.target_sim_id == sim_id, Job.status == "completed")
    )
    completed_jobs = result.scalar() or 0
    
    return {
        "sim_id": sim.id,
        "sim_number": sim.sim_number,
        "display_name": sim.display_name,
        "status": sim.status,
        "agent_status": sim.agent_status,
        "total_platform_accounts": sim.total_accounts,
        "total_jobs": total_jobs,
        "completed_jobs": completed_jobs,
        "success_rate": round(completed_jobs / total_jobs * 100, 2) if total_jobs > 0 else 0
    }
