"""
Upload Quota API Routes (Async Version)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.upload_quota import UploadQuota
from app.models.platform import Platform
from app.schemas import (
    UploadQuotaCreate,
    UploadQuotaUpdate,
    UploadQuotaResponse,
    UploadQuotaCheck,
    UploadQuotaStats,
)
from app.dependencies import get_current_user
from app.scheduler import get_scheduler_status
from app.utils.quota_reset import (
    reset_daily_quotas,
    reset_weekly_quotas,
    reset_monthly_quotas,
    get_quota_reset_stats
)


router = APIRouter(prefix="/api/v1/upload-quotas", tags=["Upload Quotas"])


def _quota_to_response(quota: UploadQuota) -> UploadQuotaResponse:
    """UploadQuota 모델을 응답 스키마로 변환"""
    return UploadQuotaResponse(
        id=quota.id,
        user_id=quota.user_id,
        platform_id=quota.platform_id,
        daily_limit=quota.daily_limit,
        weekly_limit=quota.weekly_limit,
        monthly_limit=quota.monthly_limit,
        used_today=quota.used_today,
        used_week=quota.used_week,
        used_month=quota.used_month,
        remaining_daily=quota.get_remaining_daily(),
        remaining_weekly=quota.get_remaining_weekly(),
        remaining_monthly=quota.get_remaining_monthly(),
        is_quota_exceeded=quota.is_quota_exceeded(),
        last_daily_reset=quota.last_daily_reset,
        last_weekly_reset=quota.last_weekly_reset,
        last_monthly_reset=quota.last_monthly_reset,
        created_at=quota.created_at,
        updated_at=quota.updated_at,
    )


@router.post("", response_model=UploadQuotaResponse, status_code=status.HTTP_201_CREATED)
async def create_upload_quota(
    quota_data: UploadQuotaCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    업로드 할당량 생성
    - 사용자별 플랫폼별로 하나만 생성 가능
    - 일일/주간/월간 업로드 제한 설정
    """
    # 플랫폼 존재 확인
    result = await db.execute(
        select(Platform).where(Platform.id == quota_data.platform_id)
    )
    platform = result.scalar_one_or_none()
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    
    # 기존 할당량 확인
    result = await db.execute(
        select(UploadQuota).where(
            UploadQuota.user_id == current_user.id,
            UploadQuota.platform_id == quota_data.platform_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Upload quota already exists for platform {platform.platform_name}",
        )
    
    # 새 할당량 생성
    new_quota = UploadQuota(
        user_id=current_user.id,
        platform_id=quota_data.platform_id,
        daily_limit=quota_data.daily_limit,
        weekly_limit=quota_data.weekly_limit,
        monthly_limit=quota_data.monthly_limit,
    )
    
    db.add(new_quota)
    await db.commit()
    await db.refresh(new_quota)
    
    return _quota_to_response(new_quota)


@router.get("", response_model=List[UploadQuotaResponse])
async def list_upload_quotas(
    platform_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    업로드 할당량 목록 조회
    - 현재 사용자의 모든 할당량 반환
    - platform_id로 필터링 가능
    """
    query = select(UploadQuota).where(UploadQuota.user_id == current_user.id)
    
    if platform_id:
        query = query.where(UploadQuota.platform_id == platform_id)
    
    result = await db.execute(query)
    quotas = result.scalars().all()
    return [_quota_to_response(q) for q in quotas]


@router.get("/stats/all", response_model=UploadQuotaStats)
async def get_quota_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    업로드 할당량 전체 통계
    - 총 할당량 수
    - 초과된 할당량 수
    - 플랫폼별 사용 현황
    """
    result = await db.execute(
        select(UploadQuota).where(UploadQuota.user_id == current_user.id)
    )
    quotas = result.scalars().all()
    
    total_quotas = len(quotas)
    exceeded_count = sum(1 for q in quotas if q.is_quota_exceeded())
    
    # 플랫폼별 통계
    platforms_stats = []
    for quota in quotas:
        result = await db.execute(
            select(Platform).where(Platform.id == quota.platform_id)
        )
        platform = result.scalar_one_or_none()
        platforms_stats.append({
            "platform_id": quota.platform_id,
            "platform_name": platform.platform_name if platform else "Unknown",
            "daily": {
                "used": quota.used_today,
                "limit": quota.daily_limit,
                "remaining": quota.get_remaining_daily(),
            },
            "weekly": {
                "used": quota.used_week,
                "limit": quota.weekly_limit,
                "remaining": quota.get_remaining_weekly(),
            },
            "monthly": {
                "used": quota.used_month,
                "limit": quota.monthly_limit,
                "remaining": quota.get_remaining_monthly(),
            },
            "is_exceeded": quota.is_quota_exceeded(),
        })
    
    return UploadQuotaStats(
        total_quotas=total_quotas,
        exceeded_count=exceeded_count,
        platforms=platforms_stats,
    )


@router.get("/check/{platform_id}", response_model=UploadQuotaCheck)
async def check_upload_availability(
    platform_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    업로드 가능 여부 체크
    - 할당량이 없으면 업로드 가능
    - 할당량이 있으면 초과 여부 확인
    """
    result = await db.execute(
        select(UploadQuota).where(
            UploadQuota.user_id == current_user.id,
            UploadQuota.platform_id == platform_id,
        )
    )
    quota = result.scalar_one_or_none()
    
    # 할당량 설정 없음 = 무제한
    if not quota:
        return UploadQuotaCheck(
            can_upload=True,
            reason=None,
            remaining_daily=-1,
            remaining_weekly=-1,
            remaining_monthly=-1,
            next_reset=None,
        )
    
    # 할당량 초과 확인
    if quota.is_quota_exceeded():
        reason = []
        if quota.is_daily_exceeded():
            reason.append(f"Daily limit exceeded ({quota.used_today}/{quota.daily_limit})")
        if quota.is_weekly_exceeded():
            reason.append(f"Weekly limit exceeded ({quota.used_week}/{quota.weekly_limit})")
        if quota.is_monthly_exceeded():
            reason.append(f"Monthly limit exceeded ({quota.used_month}/{quota.monthly_limit})")
        
        # 다음 리셋 시간 계산
        now = datetime.now()
        next_daily = quota.last_daily_reset + timedelta(days=1)
        next_weekly = quota.last_weekly_reset + timedelta(weeks=1)
        next_monthly = quota.last_monthly_reset + timedelta(days=30)  # 근사값
        next_reset = min(next_daily, next_weekly, next_monthly)
        
        return UploadQuotaCheck(
            can_upload=False,
            reason="; ".join(reason),
            remaining_daily=quota.get_remaining_daily(),
            remaining_weekly=quota.get_remaining_weekly(),
            remaining_monthly=quota.get_remaining_monthly(),
            next_reset=next_reset,
        )
    
    # 업로드 가능
    return UploadQuotaCheck(
        can_upload=True,
        reason=None,
        remaining_daily=quota.get_remaining_daily(),
        remaining_weekly=quota.get_remaining_weekly(),
        remaining_monthly=quota.get_remaining_monthly(),
        next_reset=None,
    )


@router.get("/{quota_id}", response_model=UploadQuotaResponse)
async def get_upload_quota(
    quota_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """업로드 할당량 상세 조회"""
    result = await db.execute(
        select(UploadQuota).where(UploadQuota.id == quota_id)
    )
    quota = result.scalar_one_or_none()
    
    if not quota:
        raise HTTPException(status_code=404, detail="Upload quota not found")
    
    # 본인 할당량만 조회 가능
    if quota.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this quota")
    
    return _quota_to_response(quota)


@router.patch("/{quota_id}", response_model=UploadQuotaResponse)
async def update_upload_quota(
    quota_id: int,
    quota_update: UploadQuotaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    업로드 할당량 수정
    - 제한값만 수정 가능 (사용량은 자동 추적)
    """
    result = await db.execute(
        select(UploadQuota).where(UploadQuota.id == quota_id)
    )
    quota = result.scalar_one_or_none()
    
    if not quota:
        raise HTTPException(status_code=404, detail="Upload quota not found")
    
    # 본인 할당량만 수정 가능
    if quota.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this quota")
    
    # 업데이트
    update_data = quota_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(quota, key, value)
    
    await db.commit()
    await db.refresh(quota)
    
    return _quota_to_response(quota)


@router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_upload_quota(
    quota_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """업로드 할당량 삭제"""
    result = await db.execute(
        select(UploadQuota).where(UploadQuota.id == quota_id)
    )
    quota = result.scalar_one_or_none()
    
    if not quota:
        raise HTTPException(status_code=404, detail="Upload quota not found")
    
    # 본인 할당량만 삭제 가능
    if quota.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this quota")
    
    await db.delete(quota)
    await db.commit()


# ==================== Scheduler & Reset Endpoints ====================

@router.get("/scheduler/status")
async def get_scheduler_status_endpoint():
    """
    스케줄러 상태 조회
    - 스케줄러가 실행 중인지 확인
    - 예약된 작업 목록 조회
    """
    return get_scheduler_status()


@router.get("/reset/stats")
async def get_reset_stats():
    """
    할당량 리셋 통계 조회
    - 전체 할당량 개수
    - 총 사용량 (일일/주간/월간)
    - 마지막 리셋 시간
    """
    stats = await get_quota_reset_stats()
    return stats


@router.post("/reset/daily", status_code=status.HTTP_200_OK)
async def manual_reset_daily(
    current_user: User = Depends(get_current_user),
):
    """
    [수동] 일일 사용량 초기화
    - 관리자 전용 (필요 시 권한 체크 추가)
    - 모든 사용자의 used_today를 0으로 초기화
    """
    try:
        rows = await reset_daily_quotas()
        return {
            "message": "Daily quotas reset successfully",
            "rows_affected": rows
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset daily quotas: {str(e)}"
        )


@router.post("/reset/weekly", status_code=status.HTTP_200_OK)
async def manual_reset_weekly(
    current_user: User = Depends(get_current_user),
):
    """
    [수동] 주간 사용량 초기화
    - 관리자 전용 (필요 시 권한 체크 추가)
    - 모든 사용자의 used_week을 0으로 초기화
    """
    try:
        rows = await reset_weekly_quotas()
        return {
            "message": "Weekly quotas reset successfully",
            "rows_affected": rows
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset weekly quotas: {str(e)}"
        )


@router.post("/reset/monthly", status_code=status.HTTP_200_OK)
async def manual_reset_monthly(
    current_user: User = Depends(get_current_user),
):
    """
    [수동] 월간 사용량 초기화
    - 관리자 전용 (필요 시 권한 체크 추가)
    - 모든 사용자의 used_month을 0으로 초기화
    """
    try:
        rows = await reset_monthly_quotas()
        return {
            "message": "Monthly quotas reset successfully",
            "rows_affected": rows
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset monthly quotas: {str(e)}"
        )
