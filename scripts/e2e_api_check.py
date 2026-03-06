import argparse
import asyncio
import json
import random
import string
import sys
from dataclasses import dataclass
from typing import Any

import requests


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


def _random_suffix(length: int = 8) -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def _add_result(results: list[CheckResult], name: str, passed: bool, detail: str) -> None:
    results.append(CheckResult(name=name, passed=passed, detail=detail))


def _extract_error(response: requests.Response) -> str:
    try:
        data = response.json()
        if isinstance(data, dict):
            return str(data.get("detail") or data.get("error") or data)
        return str(data)
    except Exception:
        return response.text[:300]


async def _check_websocket(base_url: str) -> tuple[bool, str]:
    ws_url = base_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/dashboard"

    try:
        import websockets  # type: ignore
    except Exception:
        return True, "websockets 패키지 미설치로 WS 검증은 건너뜀"

    try:
        async with websockets.connect(ws_url, open_timeout=5) as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            try:
                payload = json.loads(raw)
            except Exception:
                return False, f"WS 연결됨, 하지만 JSON 파싱 실패: {raw}"

            msg_type = payload.get("type")
            if msg_type == "connected":
                return True, "WS connected 메시지 수신"
            return False, f"WS 응답 type 불일치: {msg_type}"
    except Exception as exc:
        return False, f"WS 연결 실패: {exc}"


def run_e2e(base_url: str) -> tuple[list[CheckResult], int]:
    session = requests.Session()
    session.timeout = 10

    results: list[CheckResult] = []

    try:
        health = session.get(f"{base_url}/health", timeout=10)
    except requests.RequestException as exc:
        _add_result(results, "health", False, f"서버 연결 실패: {exc}")
        return results, 1

    if health.status_code == 200:
        _add_result(results, "health", True, "서버 health 응답 정상")
    else:
        _add_result(results, "health", False, f"status={health.status_code}, error={_extract_error(health)}")
        return results, 1

    suffix = _random_suffix()
    username = f"e2e_{suffix}"
    email = f"{username}@example.com"
    password = "Passw0rd!"

    register_payload = {
        "username": username,
        "email": email,
        "password": password,
    }
    register = session.post(f"{base_url}/api/v1/auth/register", json=register_payload, timeout=10)
    if register.status_code == 201:
        _add_result(results, "register", True, f"신규 사용자 생성: {username}")
    else:
        _add_result(results, "register", False, f"status={register.status_code}, error={_extract_error(register)}")

    login = session.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10,
    )

    if login.status_code != 200:
        _add_result(results, "login", False, f"status={login.status_code}, error={_extract_error(login)}")
        return results, 1

    token_data = login.json()
    token = token_data.get("access_token")
    if not token:
        _add_result(results, "login", False, "access_token 누락")
        return results, 1
    _add_result(results, "login", True, "JWT 발급 성공")

    auth_headers = {"Authorization": f"Bearer {token}"}

    me = session.get(f"{base_url}/api/v1/auth/me", headers=auth_headers, timeout=10)
    if me.status_code == 200:
        _add_result(results, "me", True, "토큰 검증 및 사용자 조회 성공")
    else:
        _add_result(results, "me", False, f"status={me.status_code}, error={_extract_error(me)}")

    platforms = session.get(f"{base_url}/api/v1/platforms", timeout=10)
    platform_id: int | None = None
    if platforms.status_code == 200 and isinstance(platforms.json(), list) and len(platforms.json()) > 0:
        platform_id = int(platforms.json()[0]["id"])
        _add_result(results, "platforms", True, f"플랫폼 {len(platforms.json())}건 조회")
    else:
        _add_result(results, "platforms", False, f"status={platforms.status_code}, error={_extract_error(platforms)}")

    created_job_id: int | None = None
    if platform_id is not None:
        job_payload: dict[str, Any] = {
            "platform_id": platform_id,
            "title": f"E2E Job {suffix}",
            "script": "E2E 자동 점검 스크립트입니다.",
            "source_language": "ko",
            "target_languages": ["ko"],
            "priority": 5,
        }
        create_job = session.post(f"{base_url}/api/v1/jobs", json=job_payload, headers=auth_headers, timeout=10)
        if create_job.status_code == 201:
            created_job_id = int(create_job.json().get("id"))
            _add_result(results, "create_job", True, f"Job 생성 성공 id={created_job_id}")
        else:
            _add_result(results, "create_job", False, f"status={create_job.status_code}, error={_extract_error(create_job)}")

    jobs = session.get(f"{base_url}/api/v1/jobs?limit=5", headers=auth_headers, timeout=10)
    if jobs.status_code == 200:
        _add_result(results, "jobs", True, "Job 목록 조회 성공")
    else:
        _add_result(results, "jobs", False, f"status={jobs.status_code}, error={_extract_error(jobs)}")

    agent_stats = session.get(f"{base_url}/api/v1/agents/stats", headers=auth_headers, timeout=10)
    if agent_stats.status_code == 200:
        _add_result(results, "agent_stats", True, "Agent 통계 조회 성공")
    else:
        _add_result(results, "agent_stats", False, f"status={agent_stats.status_code}, error={_extract_error(agent_stats)}")

    job_stats = session.get(f"{base_url}/api/v1/jobs/stats", headers=auth_headers, timeout=10)
    if job_stats.status_code == 200:
        _add_result(results, "job_stats", True, "Job 통계 조회 성공")
    else:
        _add_result(results, "job_stats", False, f"status={job_stats.status_code}, error={_extract_error(job_stats)}")

    ws_ok, ws_detail = asyncio.run(_check_websocket(base_url))
    _add_result(results, "websocket", ws_ok, ws_detail)

    if created_job_id is not None:
        cancel = session.put(f"{base_url}/api/v1/jobs/{created_job_id}/cancel", headers=auth_headers, timeout=10)
        if cancel.status_code == 200:
            _add_result(results, "cancel_job", True, f"Job 취소 성공 id={created_job_id}")
        else:
            _add_result(results, "cancel_job", False, f"status={cancel.status_code}, error={_extract_error(cancel)}")

    failed = [result for result in results if not result.passed]
    exit_code = 1 if failed else 0
    return results, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Admin Backend E2E API Check")
    parser.add_argument("--base-url", default="http://localhost:8001", help="Backend base URL")
    args = parser.parse_args()

    results, exit_code = run_e2e(args.base_url.rstrip("/"))

    print("\n=== E2E API CHECK REPORT ===")
    for item in results:
        mark = "PASS" if item.passed else "FAIL"
        print(f"[{mark}] {item.name}: {item.detail}")

    total = len(results)
    passed = len([r for r in results if r.passed])
    failed = total - passed
    print(f"\nSummary: {passed}/{total} passed, {failed} failed")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
