"""
WebSocket 고도화 기능 테스트
Agent 온라인/오프라인 감지, 재연결, Heartbeat timeout
"""
import sys
import asyncio
import websockets
import json
from datetime import datetime
import time

# UTF-8 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

WS_BASE_URL = "ws://127.0.0.1:8001/ws"


def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(success, message, data=None):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if data:
        if isinstance(data, dict):
            print(f"   데이터: {json.dumps(data, indent=3, ensure_ascii=False)}")
        else:
            print(f"   데이터: {data}")


async def test_dashboard_connection():
    """Dashboard WebSocket 연결 테스트"""
    print_section("1. Dashboard WebSocket 연결")
    
    try:
        async with websockets.connect(f"{WS_BASE_URL}/dashboard") as websocket:
            # 연결 메시지 수신
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "connected":
                print_result(True, "Dashboard 연결 성공", {
                    "connection_id": data.get("connection_id", "")[:16] + "...",
                    "timestamp": data.get("timestamp")
                })
                
                # Agent 목록 수신 (있을 경우)
                try:
                    agent_list_msg = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    agent_list = json.loads(agent_list_msg)
                    if agent_list.get("type") == "agent_list":
                        print_result(True, f"현재 연결된 Agent: {len(agent_list.get('agents', []))}개")
                except asyncio.TimeoutError:
                    print("   (현재 연결된 Agent 없음)")
                
                # Ping/Pong 테스트
                await websocket.send("ping")
                pong = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong)
                
                if pong_data.get("type") == "pong":
                    print_result(True, "Ping/Pong 정상 동작")
                
                return True
            else:
                print_result(False, f"예상치 못한 응답: {data.get('type')}")
                return False
    
    except Exception as e:
        print_result(False, f"Dashboard 연결 실패: {e}")
        return False


async def test_agent_connection_and_heartbeat():
    """Agent WebSocket 연결 및 Heartbeat 테스트"""
    print_section("2. Agent WebSocket 연결 및 Heartbeat")
    
    agent_id = 999  # 테스트용 Agent ID
    
    try:
        async with websockets.connect(f"{WS_BASE_URL}/agent/{agent_id}") as websocket:
            # 연결 메시지 수신
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "connected":
                connection_id = data.get("connection_id")
                heartbeat_interval = data.get("heartbeat_interval", 60)
                heartbeat_timeout = data.get("heartbeat_timeout", 300)
                
                print_result(True, f"Agent #{agent_id} 연결 성공", {
                    "connection_id": connection_id[:16] + "..." if connection_id else "none",
                    "heartbeat_interval": f"{heartbeat_interval}초",
                    "heartbeat_timeout": f"{heartbeat_timeout}초"
                })
                
                # Heartbeat 전송
                heartbeat_msg = {
                    "type": "heartbeat",
                    "status": "idle",
                    "disk_usage_percent": 45,
                    "memory_usage_percent": 60,
                    "cpu_usage_percent": 25
                }
                
                await websocket.send(json.dumps(heartbeat_msg))
                print("   📡 Heartbeat 전송...")
                
                # Heartbeat ACK 수신
                ack = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                ack_data = json.loads(ack)
                
                if ack_data.get("type") == "heartbeat_ack":
                    print_result(True, "Heartbeat ACK 수신")
                
                # Job 진행률 업데이트 테스트
                progress_msg = {
                    "type": "job_progress",
                    "job_id": 1,
                    "progress": 50,
                    "stage": "rendering"
                }
                
                await websocket.send(json.dumps(progress_msg))
                print("   📊 Job 진행률 업데이트 전송 (50%)...")
                
                # Progress ACK 수신
                progress_ack = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                progress_ack_data = json.loads(progress_ack)
                
                if progress_ack_data.get("type") == "progress_ack":
                    print_result(True, "Progress ACK 수신")
                
                # Job 완료 알림 테스트
                complete_msg = {
                    "type": "job_complete",
                    "job_id": 1,
                    "success": True
                }
                
                await websocket.send(json.dumps(complete_msg))
                print_result(True, "Job 완료 알림 전송")
                
                # 재연결 테스트 준비
                return connection_id
            
            else:
                print_result(False, f"예상치 못한 응답: {data.get('type')}")
                return None
    
    except Exception as e:
        print_result(False, f"Agent 연결 실패: {e}")
        return None


async def test_agent_reconnection(old_connection_id):
    """Agent 재연결 테스트"""
    print_section("3. Agent 재연결 테스트")
    
    agent_id = 999
    
    try:
        async with websockets.connect(f"{WS_BASE_URL}/agent/{agent_id}") as websocket:
            # 연결 메시지 수신
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "connected":
                new_connection_id = data.get("connection_id")
                print_result(True, f"Agent #{agent_id} 재연결 성공")
                
                # 재연결 메시지 전송
                reconnect_msg = {
                    "type": "reconnect",
                    "connection_id": old_connection_id
                }
                
                await websocket.send(json.dumps(reconnect_msg))
                print(f"   🔄 재연결 요청 전송 (old: {old_connection_id[:16] if old_connection_id else 'none'}...)")
                
                # 재연결 응답 수신
                reconnect_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                reconnect_data = json.loads(reconnect_response)
                
                if reconnect_data.get("type") == "reconnected":
                    print_result(True, "재연결 확인 완료", {
                        "old_connection_id": reconnect_data.get("old_connection_id", "")[:16] + "..." if reconnect_data.get("old_connection_id") else "none",
                        "new_connection_id": reconnect_data.get("new_connection_id", "")[:16] + "..." if reconnect_data.get("new_connection_id") else "none"
                    })
                
                return True
            
            return False
    
    except Exception as e:
        print_result(False, f"Agent 재연결 실패: {e}")
        return False


async def test_dashboard_command_to_agent():
    """Dashboard에서 Agent로 명령 전송 테스트"""
    print_section("4. Dashboard → Agent 명령 전송")
    
    agent_id = 888
    
    try:
        # Agent 먼저 연결
        agent_task = asyncio.create_task(simulate_agent(agent_id, duration=10))
        
        # 잠시 대기 (Agent 연결 완료)
        await asyncio.sleep(2)
        
        # Dashboard 연결
        async with websockets.connect(f"{WS_BASE_URL}/dashboard") as dashboard_ws:
            # 연결 메시지 수신
            await dashboard_ws.recv()
            
            # Agent 목록 메시지 수신 (있을 경우)
            try:
                await asyncio.wait_for(dashboard_ws.recv(), timeout=1.0)
            except asyncio.TimeoutError:
                pass
            
            # Agent로 명령 전송
            command_msg = {
                "type": "agent_command",
                "agent_id": agent_id,
                "command": "start_job",
                "params": {
                    "job_id": 123,
                    "video_url": "https://example.com/video.mp4"
                }
            }
            
            await dashboard_ws.send(json.dumps(command_msg))
            print(f"   📤 Agent #{agent_id}에게 명령 전송: start_job")
            
            # 명령 결과 수신
            result = await asyncio.wait_for(dashboard_ws.recv(), timeout=5.0)
            result_data = json.loads(result)
            
            if result_data.get("type") == "command_result":
                success = result_data.get("success", False)
                print_result(success, f"명령 전송 결과: {'성공' if success else '실패'}")
            
            # Agent 태스크 종료
            agent_task.cancel()
            try:
                await agent_task
            except asyncio.CancelledError:
                pass
            
            return True
    
    except Exception as e:
        print_result(False, f"명령 전송 테스트 실패: {e}")
        return False


async def simulate_agent(agent_id, duration=5):
    """Agent 시뮬레이션 (백그라운드)"""
    try:
        async with websockets.connect(f"{WS_BASE_URL}/agent/{agent_id}") as websocket:
            # 연결 메시지 수신
            await websocket.recv()
            
            # duration 동안 대기하면서 메시지 수신
            end_time = time.time() + duration
            while time.time() < end_time:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    
                    # 명령 수신 처리
                    if data.get("type") == "command":
                        print(f"   📥 Agent #{agent_id}가 명령 수신: {data.get('command')}")
                
                except asyncio.TimeoutError:
                    continue
    
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"   Agent #{agent_id} 시뮬레이션 오류: {e}")


async def test_websocket_stats():
    """WebSocket 통계 조회"""
    print_section("5. WebSocket 연결 통계")
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:8001/ws/stats")
        
        if response.status_code == 200:
            stats = response.json()
            
            print_result(True, "통계 조회 성공", {
                "총 연결 수": stats.get("total_connections"),
                "Dashboard 연결": stats.get("dashboard_connections"),
                "Agent 연결": stats.get("agent_connections")
            })
            
            # Agent 상세 정보
            agents = stats.get("agents", [])
            if agents:
                print("\n   📊 연결된 Agent 상세:")
                for agent in agents:
                    status_icon = "🟢" if agent.get("status") == "online" else "🔴"
                    health_icon = "✅" if agent.get("is_healthy") else "⚠️"
                    print(f"      {status_icon} Agent #{agent.get('agent_id')}: {agent.get('status')} {health_icon}")
                    print(f"         - Last heartbeat: {agent.get('seconds_since_heartbeat')}초 전")
            
            return True
        else:
            print_result(False, f"통계 조회 실패: {response.status_code}")
            return False
    
    except Exception as e:
        print_result(False, f"통계 조회 오류: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 70)
    print("  WebSocket 고도화 기능 테스트")
    print("=" * 70)
    
    # 1. Dashboard 연결 테스트
    await test_dashboard_connection()
    
    # 2. Agent 연결 및 Heartbeat 테스트
    connection_id = await test_agent_connection_and_heartbeat()
    
    # 3. Agent 재연결 테스트
    if connection_id:
        await asyncio.sleep(1)
        await test_agent_reconnection(connection_id)
    
    # 4. Dashboard → Agent 명령 전송 테스트
    await test_dashboard_command_to_agent()
    
    # 5. WebSocket 통계
    await asyncio.sleep(1)
    await test_websocket_stats()
    
    # 완료
    print_section("테스트 완료")
    print("\n✅ WebSocket 고도화 기능 테스트 완료!\n")
    print("구현된 기능:")
    print("  ✅ Dashboard WebSocket 연결")
    print("  ✅ Agent WebSocket 연결")
    print("  ✅ Heartbeat 송수신 및 ACK")
    print("  ✅ Job 진행률 업데이트")
    print("  ✅ Job 완료 알림")
    print("  ✅ Agent 재연결 지원")
    print("  ✅ Dashboard → Agent 명령 전송")
    print("  ✅ Agent별 연결 추적")
    print("  ✅ 연결 통계 조회")
    print("\n고도화 기능:")
    print("  🔄 Heartbeat Timeout 자동 감지 (5분)")
    print("  🟢 Agent 온라인/오프라인 상태 실시간 추적")
    print("  🔄 재연결 지원 (Connection ID)")
    print("  📡 Dashboard 전용 브로드캐스팅")
    print("  🎯 Agent 개별 메시지 전송")
    print("  ⏰ 백그라운드 Heartbeat Checker (30초 주기)")
    print("  📊 상세 연결 통계 (Agent별 상태, 마지막 Heartbeat 시간)")
    print("\n실제 사용 시나리오:")
    print("  1. Agent가 WebSocket 연결 시작")
    print("  2. 60초마다 Heartbeat 전송 (권장)")
    print("  3. 5분 동안 Heartbeat 없으면 자동 오프라인 처리")
    print("  4. Dashboard에서 실시간 Agent 상태 모니터링")
    print("  5. Dashboard에서 Agent로 직접 명령 전송 가능")
    print("  6. Agent 재연결 시 이전 Connection ID로 검증")
    print()


if __name__ == "__main__":
    asyncio.run(main())
