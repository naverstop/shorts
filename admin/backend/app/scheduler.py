"""
Background Scheduler for periodic tasks
- APScheduler를 사용한 주기적 작업 관리
- 일일/주간/월간 할당량 자동 초기화
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from app.utils.quota_reset import (
    reset_daily_quotas,
    reset_weekly_quotas,
    reset_monthly_quotas
)

# Global scheduler instance
scheduler = None


def init_scheduler():
    """
    스케줄러 초기화 및 작업 등록
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler
    
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")
    
    # 일일 초기화: 매일 자정 (00:00)
    scheduler.add_job(
        reset_daily_quotas,
        trigger=CronTrigger(hour=0, minute=0),
        id="daily_quota_reset",
        name="Daily Quota Reset",
        replace_existing=True
    )
    logger.info("📅 Daily quota reset scheduled: Every day at 00:00 KST")
    
    # 주간 초기화: 매주 월요일 자정 (00:00)
    scheduler.add_job(
        reset_weekly_quotas,
        trigger=CronTrigger(day_of_week='mon', hour=0, minute=0),
        id="weekly_quota_reset",
        name="Weekly Quota Reset",
        replace_existing=True
    )
    logger.info("📅 Weekly quota reset scheduled: Every Monday at 00:00 KST")
    
    # 월간 초기화: 매월 1일 자정 (00:00)
    scheduler.add_job(
        reset_monthly_quotas,
        trigger=CronTrigger(day=1, hour=0, minute=0),
        id="monthly_quota_reset",
        name="Monthly Quota Reset",
        replace_existing=True
    )
    logger.info("📅 Monthly quota reset scheduled: 1st of every month at 00:00 KST")
    
    return scheduler


def start_scheduler():
    """
    스케줄러 시작
    """
    global scheduler
    
    if scheduler is None:
        scheduler = init_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("✅ Background scheduler started successfully")
    else:
        logger.warning("Scheduler is already running")


def shutdown_scheduler():
    """
    스케줄러 종료
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        scheduler.shutdown()
        logger.info("🛑 Background scheduler stopped")


def get_scheduler_status():
    """
    스케줄러 상태 조회
    """
    global scheduler
    
    if scheduler is None:
        return {
            "running": False,
            "jobs": []
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return {
        "running": scheduler.running,
        "jobs": jobs
    }
