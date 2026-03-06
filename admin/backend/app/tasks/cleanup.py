"""
Cleanup Background Tasks

오래된 데이터를 정리하는 Celery Tasks
"""
from app.celery_app import celery_app
from datetime import datetime, timedelta
import logging
import os
import shutil
import asyncio

from sqlalchemy import select, and_

from app.database import AsyncSessionLocal
from app.models.job import Job
from app.models.agent import Agent

logger = logging.getLogger(__name__)


async def _archive_old_jobs_async(cutoff_date: datetime) -> dict:
    """완료/실패 후 오래된 Job 메타데이터에 아카이빙 마크를 추가"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Job).where(
                and_(
                    Job.completed_at.is_not(None),
                    Job.completed_at < cutoff_date,
                    Job.status.in_(["completed", "failed"]),
                )
            )
        )
        jobs = result.scalars().all()

        archived_count = 0
        archived_ids: list[int] = []
        now = datetime.now()

        for job in jobs:
            metadata = dict(job.job_metadata or {})
            if metadata.get("archived", False):
                continue

            metadata["archived"] = True
            metadata["archived_at"] = now.isoformat()
            metadata["archive_reason"] = "older_than_180_days"
            job.job_metadata = metadata
            archived_count += 1
            archived_ids.append(job.id)

        await db.commit()

        return {
            "status": "completed",
            "archived_count": archived_count,
            "archived_job_ids": archived_ids[:20],
            "cutoff_date": cutoff_date.isoformat(),
        }


async def _check_agent_disk_usage_async(threshold: int = 80) -> dict:
    """Agent 디스크 사용률 점검"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Agent))
        agents = result.scalars().all()

        high_usage_agents = [
            {
                "agent_id": agent.id,
                "device_name": agent.device_name,
                "disk_usage_percent": int(agent.disk_usage_percent or 0),
            }
            for agent in agents
            if int(agent.disk_usage_percent or 0) >= threshold
        ]

        logger.info(
            "💽 Agent disk usage checked: total=%s, cleanup_needed=%s",
            len(agents),
            len(high_usage_agents),
        )

        return {
            "status": "completed",
            "agents_checked": len(agents),
            "cleanup_needed": len(high_usage_agents),
            "threshold": threshold,
            "agents": high_usage_agents,
        }


@celery_app.task(name="app.tasks.cleanup.cleanup_old_logs")
def cleanup_old_logs():
    """
    90일 이상 오래된 로그 삭제
    
    Returns:
        dict: 삭제된 로그 수 및 처리 정보
    """
    try:
        log_dir = "logs"
        if not os.path.exists(log_dir):
            return {"status": "skipped", "reason": "log directory not found"}
        
        cutoff_date = datetime.now() - timedelta(days=90)
        deleted_count = 0
        total_size = 0
        
        for filename in os.listdir(log_dir):
            filepath = os.path.join(log_dir, filename)
            
            if os.path.isfile(filepath):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    total_size += file_size
                    logger.info(f"🗑️ Deleted old log file: {filename}")
        
        result = {
            "status": "completed",
            "deleted_files": deleted_count,
            "freed_space_mb": round(total_size / (1024 * 1024), 2),
            "cutoff_date": cutoff_date.isoformat()
        }
        
        logger.info(f"✅ Cleanup old logs completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Cleanup old logs failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.cleanup.cleanup_temp_files")
def cleanup_temp_files():
    """
    임시 파일 정리 (storage/temp/)
    
    Returns:
        dict: 삭제된 파일 수 및 처리 정보
    """
    try:
        temp_dir = "storage/temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            return {"status": "skipped", "reason": "temp directory created"}
        
        deleted_count = 0
        total_size = 0
        
        # 1일 이상 오래된 임시 파일 삭제
        cutoff_date = datetime.now() - timedelta(days=1)
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            
            if os.path.isfile(filepath):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(filepath)
                    os.remove(filepath)
                    deleted_count += 1
                    total_size += file_size
                    logger.info(f"🗑️ Deleted temp file: {filename}")
        
        result = {
            "status": "completed",
            "deleted_files": deleted_count,
            "freed_space_mb": round(total_size / (1024 * 1024), 2),
            "cutoff_date": cutoff_date.isoformat()
        }
        
        logger.info(f"✅ Cleanup temp files completed: {result}")
        return result
    
    except Exception as e:
        logger.error(f"❌ Cleanup temp files failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.cleanup.archive_old_jobs")
def archive_old_jobs():
    """
    180일 이상 완료된 Job 아카이빙
    
    완료/실패 후 180일 이상 지난 Job을 메타데이터 기준으로 아카이빙 표시
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=180)
        logger.info(f"📦 Archive old jobs task started (cutoff: {cutoff_date.isoformat()})")
        return asyncio.run(_archive_old_jobs_async(cutoff_date=cutoff_date))
    
    except Exception as e:
        logger.error(f"❌ Archive old jobs failed: {e}")
        return {"status": "error", "message": str(e)}


@celery_app.task(name="app.tasks.cleanup.check_agent_disk_usage")
def check_agent_disk_usage():
    """
    Agent 디스크 사용률 체크 및 정리 지시
    
    디스크 사용률 80% 이상 Agent 탐지
    """
    try:
        logger.info("💽 Check agent disk usage task started")
        return asyncio.run(_check_agent_disk_usage_async(threshold=80))
    
    except Exception as e:
        logger.error(f"❌ Check agent disk usage failed: {e}")
        return {"status": "error", "message": str(e)}
