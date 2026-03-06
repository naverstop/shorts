"""
Job Management API Routes
"""
import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Job, User, Agent
from app.schemas import (
    JobCreate,
    JobResponse,
    JobUpdate,
    JobAssign,
    JobStatusUpdate,
    JobStats,
    JobPublishYoutubeRequest,
    JobPublishYoutubeResponse,
    JobPublishTiktokRequest,
    JobPublishTiktokResponse,
)
from app.dependencies import get_current_user
from app.routes.websocket import manager as websocket_manager
from app.utils.quota_check import check_upload_quota
from app.config import settings
from app.services.youtube_publish_service import YouTubePublishService
from app.services.tiktok_publish_service import TikTokPublishService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    job_data: JobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new job
    - Checks upload quota before creating
    - Raises 429 if quota exceeded
    """
    # Check upload quota for target platform
    await check_upload_quota(
        user_id=current_user.id,
        platform_id=job_data.platform_id,
        db=db,
        raise_exception=True  # Will raise HTTPException if exceeded
    )
    
    job = Job(
        user_id=current_user.id,
        target_platform_id=job_data.platform_id,
        title=job_data.title,
        script=job_data.script,
        source_language=job_data.source_language,
        target_languages=job_data.target_languages,
        job_metadata=job_data.job_metadata,
        status="pending",
        priority=job_data.priority
    )
    
    db.add(job)
    await db.flush()
    await db.refresh(job)
    
    # Increment upload usage after successful job creation
    from app.utils.quota_check import increment_upload_usage
    await increment_upload_usage(
        user_id=current_user.id,
        platform_id=job_data.platform_id,
        db=db
    )
    
    return job


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, assigned, rendering, uploading, completed, failed"),
    status: Optional[str] = Query(None, description="Alias of status_filter (Agent compatibility)"),
    agent_id: Optional[int] = Query(None, description="Filter by agent ID"),
    device_id: Optional[str] = Query(None, description="Filter by assigned agent device_id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of jobs with optional filtering"""
    query = select(Job).where(Job.user_id == current_user.id)
    
    effective_status = status_filter or status
    if effective_status:
        query = query.where(Job.status == effective_status)
    
    if agent_id is not None:
        query = query.where(Job.agent_id == agent_id)

    if device_id:
        agent_result = await db.execute(select(Agent.id).where(Agent.device_id == device_id))
        target_agent_id = agent_result.scalar_one_or_none()
        if target_agent_id is None:
            return []
        query = query.where(Job.agent_id == target_agent_id)
    
    query = query.offset(skip).limit(limit).order_by(Job.created_at.desc())
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    return jobs


@router.get("/stats", response_model=JobStats)
async def get_job_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get job statistics for current user"""
    # Get total count
    result = await db.execute(
        select(func.count(Job.id)).where(Job.user_id == current_user.id)
    )
    total = result.scalar() or 0
    
    # Get count by status
    result = await db.execute(
        select(Job.status, func.count(Job.id))
        .where(Job.user_id == current_user.id)
        .group_by(Job.status)
    )
    by_status = {row[0]: row[1] for row in result.all()}
    
    # Get specific counts
    pending_count = by_status.get('pending', 0)
    processing_count = sum([
        by_status.get('assigned', 0),
        by_status.get('rendering', 0),
        by_status.get('uploading', 0)
    ])
    completed_count = by_status.get('completed', 0)
    failed_count = by_status.get('failed', 0)
    
    # Calculate average processing time for completed jobs
    result = await db.execute(
        select(func.avg(
            func.extract('epoch', Job.completed_at) - func.extract('epoch', Job.created_at)
        ))
        .where(
            Job.user_id == current_user.id,
            Job.status == 'completed',
            Job.completed_at.isnot(None)
        )
    )
    avg_processing_time = result.scalar()
    
    return JobStats(
        total=total,
        by_status=by_status,
        pending_count=pending_count,
        processing_count=processing_count,
        completed_count=completed_count,
        failed_count=failed_count,
        avg_processing_time=avg_processing_time
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get job details"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this job"
        )
    
    return job


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    job_data: JobUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update job information"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this job"
        )
    
    # Only allow update if job is pending
    if job.status not in ["pending", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update job with status: {job.status}"
        )
    
    # Update fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    await db.flush()
    await db.refresh(job)
    
    return job


@router.post("/{job_id}/assign", response_model=JobResponse)
async def assign_job(
    job_id: int,
    assign_data: JobAssign,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Assign job to an agent"""
    # Get job
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to assign this job"
        )
    
    # Check if job can be assigned
    if job.status not in ["pending", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot assign job with status: {job.status}"
        )
    
    # Check if agent exists and belongs to user
    result = await db.execute(
        select(Agent).where(Agent.id == assign_data.agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    if agent.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to use this agent"
        )
    
    # Check if agent is available
    if agent.status != "idle":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent is not available (status: {agent.status})"
        )
    
    # Assign job
    job.agent_id = assign_data.agent_id
    job.status = "assigned"
    job.assigned_at = datetime.utcnow()
    
    # Update agent status
    agent.status = "processing"
    
    await db.flush()
    await db.refresh(job)
    
    return job


@router.post("/{job_id}/status")
async def update_job_status(
    job_id: int,
    status_data: JobStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update job status (used by Agent)"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Update status
    old_status = job.status
    job.status = status_data.status
    
    if status_data.error_message:
        job.error_message = status_data.error_message

    if status_data.video_path or status_data.video_url:
        metadata = dict(job.job_metadata or {})
        if status_data.video_path:
            metadata["video_path"] = status_data.video_path
        if status_data.video_url:
            metadata["video_url"] = status_data.video_url
        job.job_metadata = metadata
    
    # Set completed_at if job is completed/failed
    if status_data.status in ["completed", "failed"]:
        job.completed_at = datetime.utcnow()
        
        # Release agent
        if job.agent_id:
            result = await db.execute(
                select(Agent).where(Agent.id == job.agent_id)
            )
            agent = result.scalar_one_or_none()
            if agent:
                agent.status = "idle"
                # Agent 상태 변경도 브로드캐스트
                await websocket_manager.broadcast_agent_update(agent.id, {
                    "status": "idle",
                    "released_from_job": job.id
                })
    
    await db.flush()
    
    # 🔥 WebSocket 브로드캐스트: Job 상태 업데이트 실시간 전송
    await websocket_manager.broadcast_job_update(job.id, {
        "old_status": old_status,
        "new_status": status_data.status,
        "error_message": status_data.error_message,
        "video_path": status_data.video_path,
        "video_url": status_data.video_url,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    })
    
    return {
        "status": "ok",
        "message": f"Job status updated from {old_status} to {status_data.status}",
        "job_id": job.id,
        "new_status": status_data.status
    }


@router.patch("/{job_id}/status")
async def update_job_status_patch(
    job_id: int,
    status_data: JobStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """PATCH alias for Agent compatibility"""
    return await update_job_status(job_id=job_id, status_data=status_data, db=db)


@router.post("/{job_id}/upload-video")
async def upload_job_video(
    job_id: int,
    video: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload rendered video file for a job"""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to upload for this job")

    ext = Path(video.filename or "video.mp4").suffix.lower()
    if ext not in {".mp4", ".mov", ".mkv", ".webm"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported video format")

    os.makedirs(settings.VIDEO_DIR, exist_ok=True)
    filename = f"job_{job.id}_{uuid4().hex}{ext}"
    target_path = os.path.join(settings.VIDEO_DIR, filename)

    file_bytes = await video.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty upload")

    with open(target_path, "wb") as output:
        output.write(file_bytes)

    metadata = dict(job.job_metadata or {})
    metadata["video_path"] = target_path
    metadata["video_filename"] = filename
    metadata["uploaded_at"] = datetime.utcnow().isoformat()
    job.job_metadata = metadata

    await db.flush()

    return {
        "status": "ok",
        "job_id": job.id,
        "video_path": target_path,
        "video_url": f"/storage/videos/{filename}",
    }


@router.post("/{job_id}/publish/youtube", response_model=JobPublishYoutubeResponse)
async def publish_job_to_youtube(
    job_id: int,
    payload: JobPublishYoutubeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish completed job video to YouTube using user's OAuth credential"""
    service = YouTubePublishService()
    try:
        result = await service.publish_job(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            credential_id=payload.credential_id,
            title=payload.title,
            description=payload.description,
            tags=payload.tags,
            privacy_status=payload.privacy_status,
        )
        return JobPublishYoutubeResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"YouTube publish failed: {str(e)}")


@router.post("/{job_id}/publish/tiktok", response_model=JobPublishTiktokResponse)
async def publish_job_to_tiktok(
    job_id: int,
    payload: JobPublishTiktokRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish completed job video to TikTok using browser automation credential"""
    service = TikTokPublishService()
    try:
        result = await service.publish_job(
            db=db,
            user_id=current_user.id,
            job_id=job_id,
            credential_id=payload.credential_id,
            caption=payload.caption,
            headless=payload.headless,
        )
        return JobPublishTiktokResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"TikTok publish failed: {str(e)}")


@router.post("/{job_id}/retry", response_model=JobResponse)
async def retry_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retry a failed job"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to retry this job"
        )
    
    # Can only retry failed jobs
    if job.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry job with status: {job.status}"
        )
    
    # Reset job status
    job.status = "pending"
    job.agent_id = None
    job.assigned_at = None
    job.completed_at = None
    job.error_message = None
    job.retry_count += 1
    
    await db.flush()
    await db.refresh(job)
    
    return job


@router.put("/{job_id}/cancel")
async def cancel_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a job"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this job"
        )
    
    if job.status in ["completed", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    # Release agent if assigned
    if job.agent_id:
        result = await db.execute(
            select(Agent).where(Agent.id == job.agent_id)
        )
        agent = result.scalar_one_or_none()
        if agent:
            agent.status = "idle"
    
    job.status = "failed"
    job.error_message = "Cancelled by user"
    job.completed_at = datetime.utcnow()
    
    await db.flush()
    
    return {"status": "ok", "message": "Job cancelled"}


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete job (only allowed for pending or completed/failed jobs)"""
    result = await db.execute(
        select(Job).where(Job.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check ownership
    if job.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job"
        )
    
    # Cannot delete jobs in progress
    if job.status in ["assigned", "rendering", "uploading"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete job in progress (status: {job.status}). Cancel it first."
        )
    
    await db.delete(job)
    await db.flush()
    
    return None
