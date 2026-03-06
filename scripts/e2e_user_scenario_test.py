"""
E2E 사용자 시나리오 테스트
실제 사용자가 수행할 주요 워크플로우를 검증
"""
import httpx
import asyncio
import time
from typing import Dict, Any


API_BASE = "http://localhost:8001/api/v1"
TEST_USER = {
    "username": "e2e_test_user",
    "email": "e2e@test.com",
    "password": "TestPassword123!",
}


class E2ETestRunner:
    def __init__(self):
        self.token = None
        self.user_id = None
        self.created_quota_id = None
        self.created_job_id = None
        self.results = []

    def log_test(self, name: str, passed: bool, message: str = ""):
        status = "✓ PASS" if passed else "✗ FAIL"
        self.results.append({"name": name, "passed": passed, "message": message})
        print(f"{status} [{name}] {message}")

    async def cleanup_test_user(self):
        """테스트 사용자 정리 (있으면 삭제)"""
        # 실제 구현은 admin API나 직접 DB 접근 필요
        # 여기서는 skip
        pass

    async def test_user_registration_and_login(self):
        """시나리오 1: 사용자 회원가입 및 로그인"""
        async with httpx.AsyncClient() as client:
            # 회원가입 시도
            try:
                response = await client.post(
                    f"{API_BASE}/auth/register", json=TEST_USER, timeout=10.0
                )
                if response.status_code == 400:
                    # 이미 존재하는 사용자 - 로그인으로 바로 진행
                    self.log_test(
                        "회원가입", True, "사용자가 이미 존재함 (로그인으로 진행)"
                    )
                else:
                    response.raise_for_status()
                    self.log_test("회원가입", True, "신규 사용자 생성 완료")
            except Exception as e:
                self.log_test("회원가입", False, str(e))
                return False

            # 로그인
            try:
                response = await client.post(
                    f"{API_BASE}/auth/login",
                    data={
                        "username": TEST_USER["username"],
                        "password": TEST_USER["password"],
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                self.token = data["access_token"]
                self.log_test("로그인", True, "JWT 토큰 발급 성공")
            except Exception as e:
                self.log_test("로그인", False, str(e))
                return False

            # 사용자 정보 조회
            try:
                response = await client.get(
                    f"{API_BASE}/auth/me",
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10.0,
                )
                response.raise_for_status()
                me_data = response.json()
                self.user_id = me_data["id"]
                self.log_test(
                    "사용자 정보 조회",
                    True,
                    f"user_id={self.user_id}, role={me_data['role']}",
                )
            except Exception as e:
                self.log_test("사용자 정보 조회", False, str(e))
                return False

        return True

    async def test_platform_and_quota_management(self):
        """시나리오 2: 플랫폼 조회 및 할당량 관리"""
        if not self.token:
            self.log_test("플랫폼/할당량 관리", False, "토큰이 없음")
            return False

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"}

            # 플랫폼 목록 조회
            try:
                response = await client.get(f"{API_BASE}/platforms", timeout=10.0)
                response.raise_for_status()
                platforms = response.json()
                youtube_platform = next(
                    (p for p in platforms if p["platform_name"].lower() == "youtube"),
                    None,
                )
                if not youtube_platform:
                    raise ValueError("YouTube 플랫폼을 찾을 수 없음")
                platform_id = youtube_platform["id"]
                self.log_test("플랫폼 조회", True, f"YouTube platform_id={platform_id}")
            except Exception as e:
                self.log_test("플랫폼 조회", False, str(e))
                return False

            # 할당량 생성
            try:
                response = await client.post(
                    f"{API_BASE}/upload-quotas",
                    headers=headers,
                    json={
                        "platform_id": platform_id,
                        "daily_limit": 5,
                        "weekly_limit": 30,
                        "monthly_limit": 100,
                    },
                    timeout=10.0,
                )
                if response.status_code == 400:
                    # 이미 존재하는 할당량
                    self.log_test("할당량 생성", True, "할당량이 이미 존재")
                else:
                    response.raise_for_status()
                    quota_data = response.json()
                    self.created_quota_id = quota_data["id"]
                    self.log_test(
                        "할당량 생성", True, f"quota_id={self.created_quota_id}"
                    )
            except Exception as e:
                self.log_test("할당량 생성", False, str(e))
                return False

            # 할당량 조회
            try:
                response = await client.get(
                    f"{API_BASE}/upload-quotas", headers=headers, timeout=10.0
                )
                response.raise_for_status()
                quotas = response.json()
                self.log_test("할당량 조회", True, f"{len(quotas)}개 할당량 확인")
            except Exception as e:
                self.log_test("할당량 조회", False, str(e))
                return False

            # 할당량 상향 (업데이트)
            if self.created_quota_id:
                try:
                    response = await client.patch(
                        f"{API_BASE}/upload-quotas/{self.created_quota_id}",
                        headers=headers,
                        json={"daily_limit": 6, "weekly_limit": 31, "monthly_limit": 101},
                        timeout=10.0,
                    )
                    response.raise_for_status()
                    self.log_test("할당량 상향", True, "daily: 5→6")
                except Exception as e:
                    self.log_test("할당량 상향", False, str(e))

        return True

    async def test_trend_and_script_workflow(self):
        """시나리오 3: 트렌드 수집 및 스크립트 생성"""
        if not self.token:
            self.log_test("트렌드/스크립트", False, "토큰이 없음")
            return False

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"}

            # 트렌드 조회
            try:
                response = await client.get(
                    f"{API_BASE}/trends?limit=3", headers=headers, timeout=10.0
                )
                response.raise_for_status()
                trends = response.json()
                self.log_test("트렌드 조회", True, f"{len(trends)}개 트렌드 확인")
            except Exception as e:
                self.log_test("트렌드 조회", False, str(e))
                return False

            # 스크립트 생성 (AI 없이 간단한 요청만 테스트)
            # 현재 scripts 엔드포인트가 다르므로 skip
            try:
                response = await client.get(
                    f"{API_BASE}/scripts?limit=1", headers=headers, timeout=10.0
                )
                response.raise_for_status()
                scripts = response.json()
                self.log_test("스크립트 조회", True, f"{len(scripts)}개 스크립트 확인")
            except Exception as e:
                self.log_test("스크립트 조회", False, str(e))

        return True

    async def test_job_lifecycle(self):
        """시나리오 4: Job 생성 및 라이프사이클 관리"""
        if not self.token:
            self.log_test("Job 라이프사이클", False, "토큰이 없음")
            return False

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"}

            # Job 생성
            try:
                response = await client.post(
                    f"{API_BASE}/jobs",
                    headers=headers,
                    json={
                        "platform_id": 1,
                        "title": "E2E Test Job",
                        "script": "This is a test script for E2E testing.",
                        "source_language": "en",
                        "target_languages": ["ko"],
                        "priority": 5,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                job_data = response.json()
                self.created_job_id = job_data["id"]
                self.log_test("Job 생성", True, f"job_id={self.created_job_id}")
            except Exception as e:
                self.log_test("Job 생성", False, str(e))
                return False

            # Job 조회
            try:
                response = await client.get(
                    f"{API_BASE}/jobs/{self.created_job_id}",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                job = response.json()
                self.log_test(
                    "Job 조회", True, f"status={job['status']}, priority={job['priority']}"
                )
            except Exception as e:
                self.log_test("Job 조회", False, str(e))
                return False

            # Job 취소
            try:
                response = await client.put(
                    f"{API_BASE}/jobs/{self.created_job_id}/cancel",
                    headers=headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                self.log_test("Job 취소", True, "Job 취소 성공")
            except Exception as e:
                self.log_test("Job 취소", False, str(e))

            # Job 목록 조회
            try:
                response = await client.get(
                    f"{API_BASE}/jobs?limit=5", headers=headers, timeout=10.0
                )
                response.raise_for_status()
                jobs = response.json()
                self.log_test("Job 목록 조회", True, f"{len(jobs)}개 Job 확인")
            except Exception as e:
                self.log_test("Job 목록 조회", False, str(e))

        return True

    async def test_agent_monitoring(self):
        """시나리오 5: Agent 모니터링"""
        if not self.token:
            self.log_test("Agent 모니터링", False, "토큰이 없음")
            return False

        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.token}"}

            # Agent 목록 조회
            try:
                response = await client.get(
                    f"{API_BASE}/agents", headers=headers, timeout=10.0
                )
                response.raise_for_status()
                agents = response.json()
                self.log_test("Agent 목록 조회", True, f"{len(agents)}개 Agent 확인")
            except Exception as e:
                self.log_test("Agent 목록 조회", False, str(e))
                return False

            # Agent 통계 조회
            try:
                response = await client.get(
                    f"{API_BASE}/agents/stats", headers=headers, timeout=10.0
                )
                response.raise_for_status()
                stats = response.json()
                self.log_test(
                    "Agent 통계",
                    True,
                    f"total={stats['total']}, online={stats['online_count']}",
                )
            except Exception as e:
                self.log_test("Agent 통계", False, str(e))

        return True

    async def run_all_scenarios(self):
        """모든 시나리오 실행"""
        print("=" * 60)
        print("🚀 E2E 사용자 시나리오 테스트 시작")
        print("=" * 60)
        print()

        start_time = time.time()

        await self.test_user_registration_and_login()
        await self.test_platform_and_quota_management()
        await self.test_trend_and_script_workflow()
        await self.test_job_lifecycle()
        await self.test_agent_monitoring()

        elapsed = time.time() - start_time

        # 결과 요약
        print()
        print("=" * 60)
        print("📊 E2E 테스트 결과 요약")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["passed"])
        failed = sum(1 for r in self.results if not r["passed"])
        total = len(self.results)

        print(f"총 테스트: {total}개")
        print(f"성공: {passed}개")
        print(f"실패: {failed}개")
        print(f"소요 시간: {elapsed:.2f}초")
        print()

        if failed > 0:
            print("실패한 테스트:")
            for r in self.results:
                if not r["passed"]:
                    print(f"  - {r['name']}: {r['message']}")
            print()

        print("=" * 60)
        if failed == 0:
            print("✅ 모든 E2E 시나리오 테스트 통과!")
        else:
            print(f"❌ {failed}개 테스트 실패")
        print("=" * 60)

        return failed == 0


async def main():
    runner = E2ETestRunner()
    success = await runner.run_all_scenarios()
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
