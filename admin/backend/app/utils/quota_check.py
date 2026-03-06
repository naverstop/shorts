"""
Upload Quota Utilities
- Quota checking functions
- Usage tracking helpers
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.upload_quota import UploadQuota
from app.models.user import User
from app.models.platform import Platform


async def check_upload_quota(
    user_id: int,
    platform_id: int,
    db: AsyncSession,
    raise_exception: bool = True
) -> tuple[bool, Optional[str]]:
    """
    사용자의 플랫폼 업로드 할당량을 체크합니다.
    
    Args:
        user_id: 사용자 ID
        platform_id: 플랫폼 ID
        db: Database session
        raise_exception: True이면 할당량 초과 시 HTTPException 발생
        
    Returns:
        (can_upload: bool, reason: Optional[str])
        - can_upload: 업로드 가능 여부
        - reason: 불가능한 경우 이유
        
    Raises:
        HTTPException: raise_exception=True이고 할당량 초과 시
    """
    # 할당량 조회
    result = await db.execute(
        select(UploadQuota).where(
            UploadQuota.user_id == user_id,
            UploadQuota.platform_id == platform_id
        )
    )
    quota = result.scalar_one_or_none()
    
    # 할당량 설정이 없으면 무제한으로 허용
    if not quota:
        return True, None
    
    # 할당량 초과 체크
    if quota.is_quota_exceeded():
        reasons = []
        
        if quota.is_daily_exceeded():
            reasons.append(
                f"Daily upload limit exceeded: {quota.used_today}/{quota.daily_limit}"
            )
        
        if quota.is_weekly_exceeded():
            reasons.append(
                f"Weekly upload limit exceeded: {quota.used_week}/{quota.weekly_limit}"
            )
        
        if quota.is_monthly_exceeded():
            reasons.append(
                f"Monthly upload limit exceeded: {quota.used_month}/{quota.monthly_limit}"
            )
        
        reason = "; ".join(reasons)
        
        if raise_exception:
            # 플랫폼 이름 가져오기
            platform_result = await db.execute(
                select(Platform).where(Platform.id == platform_id)
            )
            platform = platform_result.scalar_one_or_none()
            platform_name = platform.platform_name if platform else f"Platform {platform_id}"
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "quota_exceeded",
                    "message": f"Upload quota exceeded for {platform_name}",
                    "platform_id": platform_id,
                    "reasons": reasons,
                    "remaining": {
                        "daily": quota.get_remaining_daily(),
                        "weekly": quota.get_remaining_weekly(),
                        "monthly": quota.get_remaining_monthly()
                    }
                }
            )
        
        return False, reason
    
    # 할당량 내 - 업로드 가능
    return True, None


async def increment_upload_usage(
    user_id: int,
    platform_id: int,
    db: AsyncSession
) -> Optional[UploadQuota]:
    """
    업로드 사용량을 1 증가시킵니다.
    
    Args:
        user_id: 사용자 ID
        platform_id: 플랫폼 ID
        db: Database session
        
    Returns:
        UploadQuota: 업데이트된 할당량 객체 (할당량이 없으면 None)
    """
    result = await db.execute(
        select(UploadQuota).where(
            UploadQuota.user_id == user_id,
            UploadQuota.platform_id == platform_id
        )
    )
    quota = result.scalar_one_or_none()
    
    if not quota:
        return None
    
    # 사용량 증가
    quota.used_today += 1
    quota.used_week += 1
    quota.used_month += 1
    
    await db.commit()
    await db.refresh(quota)
    
    return quota


async def get_remaining_quota(
    user_id: int,
    platform_id: int,
    db: AsyncSession
) -> dict:
    """
    남은 할당량 정보를 조회합니다.
    
    Returns:
        {
            "has_quota": bool,
            "daily": int (-1 = unlimited),
            "weekly": int,
            "monthly": int,
            "is_exceeded": bool
        }
    """
    result = await db.execute(
        select(UploadQuota).where(
            UploadQuota.user_id == user_id,
            UploadQuota.platform_id == platform_id
        )
    )
    quota = result.scalar_one_or_none()
    
    if not quota:
        return {
            "has_quota": False,
            "daily": -1,
            "weekly": -1,
            "monthly": -1,
            "is_exceeded": False
        }
    
    return {
        "has_quota": True,
        "daily": quota.get_remaining_daily(),
        "weekly": quota.get_remaining_weekly(),
        "monthly": quota.get_remaining_monthly(),
        "is_exceeded": quota.is_quota_exceeded()
    }
