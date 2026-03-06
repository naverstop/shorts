"""
Agent Management API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, timedelta
import secrets

from app.database import get_db
from app.models import Agent, User
from app.schemas import AgentCreate, AgentResponse, AgentUpdate, AgentHeartbeat, AgentStats
from app.dependencies import get_current_user
from app.routes.websocket import manager as websocket_manager

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent (Android device)"""
    # Check if device_id already exists
    result = await db.execute(
        select(Agent).where(Agent.device_id == agent_data.device_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID already registered"
        )
    
    # Generate API key
    api_key = secrets.token_urlsafe(32)
    
    # Generate device name: USER{id}_AGENT{seq}_{carrier}
    result = await db.execute(
        select(func.count(Agent.id)).where(Agent.user_id == current_user.id)
    )
    agent_count = result.scalar() or 0
    device_name = f"USER{current_user.id}_AGENT{agent_count + 1}"
    if agent_data.sim_carrier:
        device_name += f"_{agent_data.sim_carrier}"
    
    # Create agent
    agent = Agent(
        user_id=current_user.id,
        device_id=agent_data.device_id,
        device_name=agent_data.device_name or device_name,
        api_key=api_key,
        sim_carrier=agent_data.sim_carrier,
        android_version=agent_data.android_version,
        apk_version=agent_data.apk_version,
        status="idle"
    )
    
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    
    return agent


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, description="Filter by status: idle, processing, offline, banned"),
    device_id: Optional[str] = Query(None, description="Filter by device_id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of agents with optional filtering"""
    query = select(Agent).where(Agent.user_id == current_user.id)
    
    # Apply status filter
    if status_filter:
        query = query.where(Agent.status == status_filter)

    if device_id:
        query = query.where(Agent.device_id == device_id)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    agents = result.scalars().all()
    return agents


@router.post("/heartbeat")
async def agent_heartbeat_by_device_id(
    heartbeat_data: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Update heartbeat using device_id payload (Agent SDK compatibility)
    Expected payload example:
    {
      "device_id": "...",
      "status": "online|busy|offline|error",
      "storage_available": 20,
      "battery_level": 80
    }
    """
    payload_device_id = heartbeat_data.get("device_id")
    if not payload_device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="device_id is required"
        )

    result = await db.execute(
        select(Agent).where(Agent.device_id == payload_device_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )

    agent.last_heartbeat = datetime.utcnow()

    payload_status = heartbeat_data.get("status")
    status_map = {
        "online": "idle",
        "busy": "processing",
        "offline": "offline",
        "error": "banned",
        "idle": "idle",
        "processing": "processing",
        "banned": "banned",
    }
    if payload_status:
        mapped_status = status_map.get(str(payload_status).lower())
        if mapped_status:
            agent.status = mapped_status

    storage_available = heartbeat_data.get("storage_available")
    if storage_available is not None:
        try:
            storage_available_gb = float(storage_available)
            estimated_total_gb = 128.0
            used_percent = int(max(0.0, min(100.0, (1 - (storage_available_gb / estimated_total_gb)) * 100.0)))
            agent.disk_usage_percent = used_percent
        except (TypeError, ValueError):
            pass

    if request.client:
        agent.ip_address = request.client.host

    await db.flush()

    await websocket_manager.broadcast_agent_update(agent.id, {
        "status": agent.status,
        "disk_usage_percent": agent.disk_usage_percent,
        "ip_address": str(agent.ip_address) if agent.ip_address else None,
        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
    })

    return {
        "status": "ok",
        "message": "Heartbeat received",
        "agent_id": agent.id,
        "agent_status": agent.status,
        "last_heartbeat": agent.last_heartbeat,
    }


@router.get("/stats", response_model=AgentStats)
async def get_agent_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent statistics for current user"""
    # Get total count
    result = await db.execute(
        select(func.count(Agent.id)).where(Agent.user_id == current_user.id)
    )
    total = result.scalar() or 0
    
    # Get count by status
    result = await db.execute(
        select(Agent.status, func.count(Agent.id))
        .where(Agent.user_id == current_user.id)
        .group_by(Agent.status)
    )
    by_status = {row[0]: row[1] for row in result.all()}
    
    # Get online count (heartbeat within last 5 minutes)
    five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
    result = await db.execute(
        select(func.count(Agent.id))
        .where(
            Agent.user_id == current_user.id,
            Agent.last_heartbeat >= five_minutes_ago
        )
    )
    online_count = result.scalar() or 0
    offline_count = total - online_count
    
    return AgentStats(
        total=total,
        by_status=by_status,
        online_count=online_count,
        offline_count=offline_count
    )


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get agent details"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check ownership
    if agent.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this agent"
        )
    
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update agent information"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check ownership
    if agent.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this agent"
        )
    
    # Update fields
    update_data = agent_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(agent, field, value)
    
    await db.flush()
    await db.refresh(agent)
    
    return agent


@router.post("/{agent_id}/heartbeat")
async def agent_heartbeat(
    agent_id: int,
    heartbeat_data: AgentHeartbeat,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Update agent heartbeat with optional metrics"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Update heartbeat
    agent.last_heartbeat = datetime.utcnow()
    
    # Update optional metrics
    if heartbeat_data.disk_usage_percent is not None:
        agent.disk_usage_percent = heartbeat_data.disk_usage_percent
    if heartbeat_data.apk_version:
        agent.apk_version = heartbeat_data.apk_version
    if heartbeat_data.android_version:
        agent.android_version = heartbeat_data.android_version
    
    # Update IP address from request
    if request.client:
        agent.ip_address = request.client.host
    
    # Auto-update status based on previous status
    if agent.status == "offline":
        agent.status = "idle"
    
    await db.flush()
    
    # 🔥 WebSocket 브로드캐스트: Agent 상태 업데이트 실시간 전송
    await websocket_manager.broadcast_agent_update(agent_id, {
        "status": agent.status,
        "disk_usage_percent": agent.disk_usage_percent,
        "ip_address": str(agent.ip_address) if agent.ip_address else None,
        "last_heartbeat": agent.last_heartbeat.isoformat() if agent.last_heartbeat else None,
        "apk_version": agent.apk_version
    })
    
    return {
        "status": "ok",
        "message": "Heartbeat received",
        "agent_status": agent.status,
        "last_heartbeat": agent.last_heartbeat
    }


@router.post("/{agent_id}/regenerate-key", response_model=AgentResponse)
async def regenerate_api_key(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate agent API key"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check ownership
    if agent.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to regenerate key for this agent"
        )
    
    # Generate new API key
    agent.api_key = secrets.token_urlsafe(32)
    
    await db.flush()
    await db.refresh(agent)
    
    return agent


@router.post("/{agent_id}/disk-cleanup")
async def record_disk_cleanup(
    agent_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Record that disk cleanup was performed"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    agent.last_disk_cleanup = datetime.utcnow()
    agent.disk_usage_percent = 0  # Reset after cleanup
    
    await db.flush()
    
    return {
        "status": "ok",
        "message": "Disk cleanup recorded",
        "last_cleanup": agent.last_disk_cleanup
    }


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete agent"""
    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check ownership
    if agent.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this agent"
        )
    
    await db.delete(agent)
    await db.flush()
    
    return None
