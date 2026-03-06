"""
AI Integration API 테스트 스크립트
트렌드 수집, 스크립트 생성, 유사도 검색을 테스트합니다.
"""
import asyncio
import httpx
from datetime import datetime


BASE_URL = "http://localhost:8001/api/v1"
TEST_USER = {
    "username": f"aitest_{datetime.now().strftime('%H%M%S')}",
    "email": f"aitest_{datetime.now().strftime('%H%M%S')}@test.com",
    "password": "test1234"
}


async def register_and_login():
    """테스트 사용자 등록 및 로그인"""
    async with httpx.AsyncClient() as client:
        # 회원가입
        print("\n📝 테스트 사용자 생성 중...")
        resp = await client.post(f"{BASE_URL}/auth/register", json=TEST_USER)
        if resp.status_code == 200:
            print(f"✅ 회원가입 성공: {TEST_USER['username']}")
        else:
            print(f"⚠️ 회원가입 실패 (이미 존재하거나 오류): {resp.status_code}")
        
        # 로그인
        print("\n🔐 로그인 중...")
        resp = await client.post(
            f"{BASE_URL}/auth/login",
            data={"username": TEST_USER["username"], "password": TEST_USER["password"]}
        )
        if resp.status_code == 200:
            token = resp.json()["access_token"]
            print("✅ 로그인 성공")
            return token
        else:
            raise Exception(f"로그인 실패: {resp.status_code}")


async def test_trend_collection(token: str):
    """트렌드 수집 테스트"""
    print("\n" + "="*60)
    print("📊 트렌드 수집 API 테스트")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 트렌드 수집 시작
        print("\n1️⃣ YouTube 트렌드 수집 시작...")
        try:
            resp = await client.post(
                f"{BASE_URL}/trends/collect",
                json={"region_code": "KR", "category_id": None, "max_results": 10},
                headers=headers
            )
            if resp.status_code == 200:
                result = resp.json()
                print(f"✅ 트렌드 수집 완료: {result['collected_count']}개")
                print(f"   메시지: {result['message']}")
            else:
                print(f"❌ 트렌드 수집 실패: {resp.status_code}")
                print(f"   응답: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 트렌드 수집 오류: {str(e)}")
            return None
        
        # 2. 트렌드 목록 조회
        print("\n2️⃣ 트렌드 목록 조회...")
        resp = await client.get(
            f"{BASE_URL}/trends?source=youtube&limit=5",
            headers=headers
        )
        if resp.status_code == 200:
            trends = resp.json()
            print(f"✅ 트렌드 {len(trends)}개 조회")
            for i, trend in enumerate(trends[:3], 1):
                print(f"   {i}. {trend['keyword']} (점수: {trend['trend_score']})")
            return trends[0] if trends else None
        else:
            print(f"❌ 트렌드 조회 실패: {resp.status_code}")
            return None


async def test_script_generation(token: str, trend_id: int = None):
    """스크립트 생성 테스트"""
    print("\n" + "="*60)
    print("✍️ AI 스크립트 생성 테스트")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. 스크립트 생성
        print("\n1️⃣ AI 스크립트 생성 시작...")
        script_data = {
            "topic": "2026년 AI 트렌드",
            "trend_id": trend_id,
            "target_audience": "20-30대 개발자",
            "platform": "youtube_shorts",
            "language": "ko",
            "duration": 30
        }
        
        try:
            resp = await client.post(
                f"{BASE_URL}/scripts",
                json=script_data,
                headers=headers
            )
            if resp.status_code == 200:
                script = resp.json()
                print(f"✅ 스크립트 생성 완료: {script['title']}")
                print(f"   ID: {script['id']}")
                print(f"   Hook: {script['hook'][:50]}...")
                print(f"   생성 모델: {script['ai_model']}")
                return script
            else:
                print(f"❌ 스크립트 생성 실패: {resp.status_code}")
                print(f"   응답: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 스크립트 생성 오류: {str(e)}")
            return None


async def test_similarity_search(token: str, script_id: int):
    """유사도 검색 테스트"""
    print("\n" + "="*60)
    print("🔍 Vector 유사도 검색 테스트")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 유사 스크립트 검색
        print(f"\n1️⃣ Script ID {script_id}와 유사한 스크립트 검색...")
        resp = await client.get(
            f"{BASE_URL}/scripts/{script_id}/similar?threshold=0.85&limit=5",
            headers=headers
        )
        if resp.status_code == 200:
            similar_scripts = resp.json()
            print(f"✅ 유사 스크립트 {len(similar_scripts)}개 발견")
            for i, item in enumerate(similar_scripts, 1):
                script = item["script"]
                similarity = item["similarity"]
                print(f"   {i}. {script['title']}")
                print(f"      유사도: {similarity:.2%}")
        else:
            print(f"❌ 유사도 검색 실패: {resp.status_code}")


async def test_script_list(token: str):
    """스크립트 목록 조회 테스트"""
    print("\n" + "="*60)
    print("📋 내 스크립트 목록 조회")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BASE_URL}/scripts", headers=headers)
        if resp.status_code == 200:
            scripts = resp.json()
            print(f"✅ 내 스크립트 {len(scripts)}개 조회")
            for i, script in enumerate(scripts, 1):
                print(f"   {i}. {script['title']}")
                print(f"      생성일: {script['created_at']}")
        else:
            print(f"❌ 스크립트 목록 조회 실패: {resp.status_code}")


async def main():
    """전체 테스트 실행"""
    print("\n" + "="*60)
    print("🚀 AI Integration API 통합 테스트 시작")
    print("="*60)
    
    try:
        # 1. 로그인
        token = await register_and_login()
        
        # 2. 트렌드 수집 테스트
        trend = await test_trend_collection(token)
        trend_id = trend["id"] if trend else None
        
        # 3. 스크립트 생성 테스트
        script = await test_script_generation(token, trend_id)
        
        # 4. 유사도 검색 테스트 (스크립트가 생성되었다면)
        if script:
            await test_similarity_search(token, script["id"])
        
        # 5. 스크립트 목록 조회
        await test_script_list(token)
        
        print("\n" + "="*60)
        print("✅ 전체 테스트 완료!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n⚠️ 주의: 이 테스트를 실행하기 전에:")
    print("  1. .env 파일에 실제 API 키를 설정하세요")
    print("  2. FastAPI 서버가 실행 중인지 확인하세요 (port 8001)")
    print("  3. PostgreSQL 및 pgvector가 설치되어 있는지 확인하세요\n")
    
    input("계속하려면 Enter를 누르세요...")
    
    asyncio.run(main())
