"""
WebSocket Real-time Communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, BackgroundTasks
from typing import List, Dict, Optional
import json
import logging
import asyncio
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_info: Dict[WebSocket, dict] = {}
        self.agent_connections: Dict[int, dict] = {}  # agent_id -> {websocket, last_heartbeat, connection_id}
        self.dashboard_connections: List[WebSocket] = []
        self._heartbeat_check_task: Optional[asyncio.Task] = None
    
    async def connect(self, websocket: WebSocket, client_type: str = "dashboard", agent_id: Optional[int] = None):
        """클라이언트 연결"""
        await websocket.accept()
        self.active_connections.append(websocket)
        
        connection_id = str(uuid.uuid4())
        
        self.connection_info[websocket] = {
            "type": client_type,
            "agent_id": agent_id,
            "connected_at": datetime.now(),
            "connection_id": connection_id,
            "last_activity": datetime.now()
        }
        
        # Agent 연결 추적
        if client_type.startswith("agent_") and agent_id:
            self.agent_connections[agent_id] = {
                "websocket": websocket,
                "last_heartbeat": datetime.now(),
                "connection_id": connection_id,
                "status": "online"
            }
            # Dashboard에 Agent 온라인 알림
            await self.broadcast_to_dashboards({
                "type": "agent_status",
                "agent_id": agent_id,
                "status": "online",
                "timestamp": datetime.now().isoformat()
            })
        elif client_type == "dashboard":
            self.dashboard_connections.append(websocket)
        
        logger.info(f"✅ WebSocket connected: {client_type} (ID: {connection_id[:8]}..., total: {len(self.active_connections)})")
        
        # Heartbeat 체크 태스크 시작 (첫 연결 시)
        if self._heartbeat_check_task is None or self._heartbeat_check_task.done():
            self._heartbeat_check_task = asyncio.create_task(self._heartbeat_checker())
        
        return connection_id
    
    def disconnect(self, websocket: WebSocket):
        """클라이언트 연결 해제"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_info = self.connection_info.pop(websocket, {})
            
            # Agent 연결 해제 처리
            agent_id = client_info.get("agent_id")
            if agent_id and agent_id in self.agent_connections:
                del self.agent_connections[agent_id]
                # Dashboard에 Agent 오프라인 알림 (비동기 안전하게)
                asyncio.create_task(self.broadcast_to_dashboards({
                    "type": "agent_status",
                    "agent_id": agent_id,
                    "status": "offline",
                    "timestamp": datetime.now().isoformat()
                }))
            
            # Dashboard 연결 해제
            if websocket in self.dashboard_connections:
                self.dashboard_connections.remove(websocket)
            
            logger.info(f"❌ WebSocket disconnected: {client_info.get('type', 'unknown')} (total: {len(self.active_connections)})")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """개별 클라이언트에게 메시지 전송"""
        try:
            await websocket.send_json(message)
            # 활동 시간 업데이트
            if websocket in self.connection_info:
                self.connection_info[websocket]["last_activity"] = datetime.now()
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict, exclude: WebSocket = None):
        """모든 연결된 클라이언트에게 메시지 브로드캐스트"""
        disconnected = []
        for connection in self.active_connections:
            if connection != exclude:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to client: {e}")
                    disconnected.append(connection)
        
        # 연결 실패한 클라이언트 제거
        for conn in disconnected:
            self.disconnect(conn)
    
    async def broadcast_to_dashboards(self, message: dict):
        """Dashboard 클라이언트들에게만 브로드캐스트"""
        disconnected = []
        for connection in self.dashboard_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to dashboard: {e}")
                disconnected.append(connection)
        
        # 연결 실패한 클라이언트 제거
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_to_agent(self, agent_id: int, message: dict) -> bool:
        """특정 Agent에게 메시지 전송"""
        if agent_id in self.agent_connections:
            agent_conn = self.agent_connections[agent_id]
            websocket = agent_conn["websocket"]
            try:
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Failed to send to Agent #{agent_id}: {e}")
                self.disconnect(websocket)
                return False
        return False
    
    def update_agent_heartbeat(self, agent_id: int):
        """Agent heartbeat 시간 업데이트"""
        if agent_id in self.agent_connections:
            self.agent_connections[agent_id]["last_heartbeat"] = datetime.now()
            self.agent_connections[agent_id]["status"] = "online"
    
    async def _heartbeat_checker(self):
        """백그라운드 태스크: Agent heartbeat timeout 체크"""
        logger.info("🔄 Heartbeat checker started")
        
        while True:
            try:
                await asyncio.sleep(30)  # 30초마다 체크
                
                now = datetime.now()
                timeout_threshold = timedelta(minutes=5)  # 5분 timeout
                
                offline_agents = []
                for agent_id, conn_info in list(self.agent_connections.items()):
                    last_heartbeat = conn_info["last_heartbeat"]
                    time_since_heartbeat = now - last_heartbeat
                    
                    if time_since_heartbeat > timeout_threshold and conn_info["status"] == "online":
                        # Agent timeout!
                        conn_info["status"] = "offline"
                        offline_agents.append(agent_id)
                        logger.warning(f"⚠️  Agent #{agent_id} heartbeat timeout ({time_since_heartbeat.seconds}s)")
                        
                        # Dashboard에 오프라인 알림
                        await self.broadcast_to_dashboards({
                            "type": "agent_status",
                            "agent_id": agent_id,
                            "status": "offline",
                            "reason": "heartbeat_timeout",
                            "last_heartbeat": last_heartbeat.isoformat(),
                            "timestamp": now.isoformat()
                        })
                
                if offline_agents:
                    logger.info(f"🔴 Marked {len(offline_agents)} agents as offline due to timeout")
                
            except asyncio.CancelledError:
                logger.info("🛑 Heartbeat checker stopped")
                break
            except Exception as e:
                logger.error(f"❌ Error in heartbeat checker: {e}")
    
    async def broadcast_agent_update(self, agent_id: int, data: dict):
        """Agent 상태 업데이트 브로드캐스트"""
        message = {
            "type": "agent_update",
            "agent_id": agent_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_dashboards(message)
        logger.debug(f"📡 Broadcasted agent update: Agent #{agent_id}")
    
    async def broadcast_job_update(self, job_id: int, data: dict):
        """Job 상태 업데이트 브로드캐스트"""
        message = {
            "type": "job_update",
            "job_id": job_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self.broadcast_to_dashboards(message)
        logger.debug(f"📡 Broadcasted job update: Job #{job_id}")
    
    def get_stats(self) -> dict:
        """연결 통계"""
        agent_stats = []
        for agent_id, conn_info in self.agent_connections.items():
            last_heartbeat = conn_info["last_heartbeat"]
            time_since_heartbeat = datetime.now() - last_heartbeat
            
            agent_stats.append({
                "agent_id": agent_id,
                "status": conn_info["status"],
                "connection_id": conn_info["connection_id"],
                "last_heartbeat": last_heartbeat.isoformat(),
                "seconds_since_heartbeat": int(time_since_heartbeat.total_seconds()),
                "is_healthy": time_since_heartbeat < timedelta(minutes=5)
            })
        
        return {
            "total_connections": len(self.active_connections),
            "dashboard_connections": len(self.dashboard_connections),
            "agent_connections": len(self.agent_connections),
            "agents": agent_stats,
            "connections": [
                {
                    "type": self.connection_info[conn].get("type"),
                    "connection_id": self.connection_info[conn].get("connection_id"),
                    "connected_at": self.connection_info[conn].get("connected_at").isoformat(),
                    "last_activity": self.connection_info[conn].get("last_activity").isoformat()
                }
                for conn in self.active_connections
            ]
        }


# 전역 ConnectionManager 인스턴스
manager = ConnectionManager()


@router.websocket("/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """
    Dashboard용 WebSocket 연결
    
    실시간으로 Agent 상태, Job 진행률 등을 받습니다.
    """
    connection_id = await manager.connect(websocket, client_type="dashboard")
    
    try:
        # 연결 성공 메시지 전송
        await manager.send_personal_message({
            "type": "connected",
            "message": "Dashboard WebSocket connected",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # 현재 연결된 Agent 목록 전송
        agent_list = []
        for agent_id, conn_info in manager.agent_connections.items():
            agent_list.append({
                "agent_id": agent_id,
                "status": conn_info["status"],
                "last_heartbeat": conn_info["last_heartbeat"].isoformat()
            })
        
        if agent_list:
            await manager.send_personal_message({
                "type": "agent_list",
                "agents": agent_list,
                "timestamp": datetime.now().isoformat()
            }, websocket)
        
        # 클라이언트로부터 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            
            # Ping/Pong 처리
            if data == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            else:
                try:
                    message = json.loads(data)
                    msg_type = message.get("type")
                    
                    # Dashboard에서 Agent로 명령 전송
                    if msg_type == "agent_command":
                        agent_id = message.get("agent_id")
                        command = message.get("command")
                        
                        if agent_id and command:
                            success = await manager.send_to_agent(agent_id, {
                                "type": "command",
                                "command": command,
                                "params": message.get("params", {}),
                                "timestamp": datetime.now().isoformat()
                            })
                            
                            # 결과 응답
                            await manager.send_personal_message({
                                "type": "command_result",
                                "agent_id": agent_id,
                                "success": success,
                                "timestamp": datetime.now().isoformat()
                            }, websocket)
                    
                    else:
                        logger.info(f"📩 Received from dashboard: {data}")
                
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from dashboard: {data}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)


@router.websocket("/agent/{agent_id}")
async def websocket_agent(websocket: WebSocket, agent_id: int):
    """
    Agent용 WebSocket 연결
    
    Agent가 실시간으로 상태를 보고하고 명령을 받습니다.
    """
    connection_id = await manager.connect(websocket, client_type=f"agent_{agent_id}", agent_id=agent_id)
    
    try:
        # 연결 성공 메시지 전송
        await manager.send_personal_message({
            "type": "connected",
            "message": f"Agent #{agent_id} WebSocket connected",
            "agent_id": agent_id,
            "connection_id": connection_id,
            "heartbeat_interval": 60,  # 권장 heartbeat 간격 (초)
            "heartbeat_timeout": 300,  # Timeout 시간 (초)
            "timestamp": datetime.now().isoformat()
        }, websocket)
        
        # Agent로부터 메시지 수신 대기
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 메시지 타입별 처리
            msg_type = message.get("type")
            
            if msg_type == "heartbeat":
                # Heartbeat 수신 - 시간 업데이트
                manager.update_agent_heartbeat(agent_id)
                
                # Heartbeat 응답
                await manager.send_personal_message({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
                
                # Dashboard로 Agent 상태 브로드캐스트
                await manager.broadcast_agent_update(agent_id, {
                    "status": message.get("status", "online"),
                    "disk_usage_percent": message.get("disk_usage_percent"),
                    "memory_usage_percent": message.get("memory_usage_percent"),
                    "cpu_usage_percent": message.get("cpu_usage_percent"),
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "job_progress":
                # Job 진행률 업데이트
                job_id = message.get("job_id")
                progress = message.get("progress", 0)
                stage = message.get("stage", "unknown")
                
                await manager.broadcast_job_update(job_id, {
                    "agent_id": agent_id,
                    "progress": progress,
                    "stage": stage,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 진행률 수신 확인
                await manager.send_personal_message({
                    "type": "progress_ack",
                    "job_id": job_id,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif msg_type == "job_complete":
                # Job 완료 알림
                job_id = message.get("job_id")
                success = message.get("success", True)
                
                await manager.broadcast_job_update(job_id, {
                    "agent_id": agent_id,
                    "status": "completed" if success else "failed",
                    "error": message.get("error"),
                    "timestamp": datetime.now().isoformat()
                })
            
            elif msg_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            elif msg_type == "reconnect":
                # 재연결 요청 - 이전 연결 ID 확인
                old_connection_id = message.get("connection_id")
                logger.info(f"🔄 Agent #{agent_id} reconnecting (old: {old_connection_id[:8] if old_connection_id else 'none'}...)")
                
                # 재연결 성공 응답
                await manager.send_personal_message({
                    "type": "reconnected",
                    "message": "Reconnection successful",
                    "old_connection_id": old_connection_id,
                    "new_connection_id": connection_id,
                    "timestamp": datetime.now().isoformat()
                }, websocket)
            
            else:
                logger.info(f"📩 Received from Agent #{agent_id}: {msg_type}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error for Agent #{agent_id}: {e}")
        manager.disconnect(websocket)


@router.get("/stats")
async def get_websocket_stats():
    """WebSocket 연결 통계"""
    return manager.get_stats()
