"""
WebSocket Connection Test Script
"""
import asyncio
import websockets
import json
from datetime import datetime


async def test_dashboard_websocket():
    """Dashboard WebSocket 연결 테스트"""
    uri = "ws://127.0.0.1:8001/ws/dashboard"
    
    print("🔌 Connecting to Dashboard WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Dashboard WebSocket!")
            
            # 연결 메시지 수신
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📩 Received: {json.dumps(data, indent=2)}")
            
            # Ping 전송
            print("\n🏓 Sending ping...")
            await websocket.send("ping")
            
            # Pong 수신
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📩 Received pong: {json.dumps(data, indent=2)}")
            
            # 5초간 대기하며 메시지 수신
            print("\n⏳ Waiting for 5 seconds to receive broadcasts...")
            try:
                async with asyncio.timeout(5):
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        print(f"📡 Broadcast: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("⏰ Timeout - no broadcasts received (normal if no activity)")
            
            print("\n✅ Dashboard WebSocket test completed!")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_agent_websocket():
    """Agent WebSocket 연결 테스트"""
    agent_id = 1
    uri = f"ws://127.0.0.1:8001/ws/agent/{agent_id}"
    
    print(f"\n🔌 Connecting to Agent #{agent_id} WebSocket...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ Connected to Agent #{agent_id} WebSocket!")
            
            # 연결 메시지 수신
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📩 Received: {json.dumps(data, indent=2)}")
            
            # Heartbeat 전송
            print("\n💓 Sending heartbeat...")
            heartbeat = {
                "type": "heartbeat",
                "status": "idle",
                "disk_usage_percent": 45,
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(heartbeat))
            print(f"📤 Sent: {json.dumps(heartbeat, indent=2)}")
            
            # Job Progress 전송
            print("\n📊 Sending job progress...")
            progress = {
                "type": "job_progress",
                "job_id": 1,
                "progress": 50,
                "stage": "rendering",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(progress))
            print(f"📤 Sent: {json.dumps(progress, indent=2)}")
            
            # Ping 전송
            print("\n🏓 Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Pong 수신
            message = await websocket.recv()
            data = json.loads(message)
            print(f"📩 Received pong: {json.dumps(data, indent=2)}")
            
            print(f"\n✅ Agent #{agent_id} WebSocket test completed!")
    
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_stats_endpoint():
    """WebSocket 통계 엔드포인트 테스트"""
    import httpx
    
    print("\n📊 Fetching WebSocket stats...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://127.0.0.1:8001/ws/stats")
            data = response.json()
            print(f"✅ Stats: {json.dumps(data, indent=2)}")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """메인 테스트 실행"""
    print("=" * 60)
    print("🧪 WebSocket Integration Test")
    print("=" * 60)
    
    # Dashboard WebSocket 테스트
    await test_dashboard_websocket()
    
    # Agent WebSocket 테스트
    await test_agent_websocket()
    
    # Stats 엔드포인트 테스트
    await test_stats_endpoint()
    
    print("\n" + "=" * 60)
    print("✅ All WebSocket tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
