"""
Upload Quota Reset Utilities
- 일일/주간/월간 사용량 자동 초기화
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.models.upload_quota import UploadQuota
from app.database import AsyncSessionLocal


async def reset_daily_quotas():
    """
    모든 사용자의 일일 사용량 초기화
    - used_today를 0으로 리셋
    - last_daily_reset 업데이트
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            
            # 모든 할당량의 일일 사용량 초기화
            result = await db.execute(
                update(UploadQuota)
                .values(
                    used_today=0,
                    last_daily_reset=now
                )
            )
            
            await db.commit()
            
            rows_affected = result.rowcount
            logger.info(f"✅ Daily quota reset completed: {rows_affected} records updated")
            return rows_affected
            
        except Exception as e:
            logger.error(f"❌ Daily quota reset failed: {e}")
            await db.rollback()
            raise


async def reset_weekly_quotas():
    """
    모든 사용자의 주간 사용량 초기화
    - used_week을 0으로 리셋
    - last_weekly_reset 업데이트
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            
            # 모든 할당량의 주간 사용량 초기화
            result = await db.execute(
                update(UploadQuota)
                .values(
                    used_week=0,
                    last_weekly_reset=now
                )
            )
            
            await db.commit()
            
            rows_affected = result.rowcount
            logger.info(f"✅ Weekly quota reset completed: {rows_affected} records updated")
            return rows_affected
            
        except Exception as e:
            logger.error(f"❌ Weekly quota reset failed: {e}")
            await db.rollback()
            raise


async def reset_monthly_quotas():
    """
    모든 사용자의 월간 사용량 초기화
    - used_month를 0으로 리셋
    - last_monthly_reset 업데이트
    """
    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now(timezone.utc)
            
            # 모든 할당량의 월간 사용량 초기화
            result = await db.execute(
                update(UploadQuota)
                .values(
                    used_month=0,
                    last_monthly_reset=now
                )
            )
            
            await db.commit()
            
            rows_affected = result.rowcount
            logger.info(f"✅ Monthly quota reset completed: {rows_affected} records updated")
            return rows_affected
            
        except Exception as e:
            logger.error(f"❌ Monthly quota reset failed: {e}")
            await db.rollback()
            raise


async def get_quota_reset_stats():
    """
    할당량 리셋 통계 조회
    """
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(UploadQuota))
            quotas = result.scalars().all()
            
            if not quotas:
                return {
                    "total_quotas": 0,
                    "total_used_today": 0,
                    "total_used_week": 0,
                    "total_used_month": 0
                }
            
            return {
                "total_quotas": len(quotas),
                "total_used_today": sum(q.used_today for q in quotas),
                "total_used_week": sum(q.used_week for q in quotas),
                "total_used_month": sum(q.used_month for q in quotas),
                "last_daily_reset": max(q.last_daily_reset for q in quotas) if quotas else None,
                "last_weekly_reset": max(q.last_weekly_reset for q in quotas) if quotas else None,
                "last_monthly_reset": max(q.last_monthly_reset for q in quotas) if quotas else None
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get quota reset stats: {e}")
            raise
