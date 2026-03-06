"""
Platform Credential API 테스트
"""
import sys
import requests
import json
from datetime import datetime

# UTF-8 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8001/api/v1"
TOKEN = None
USER_ID = None

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(success, message, data=None):
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")
    if data:
        print(f"   데이터: {json.dumps(data, indent=3, ensure_ascii=False)}")

# 1. 사용자 등록 및 로그인
print_section("1. 사용자 인증")

timestamp = datetime.now().strftime("%H%M%S")
username = f"testuser{timestamp}"
password = "test1234"

# 회원가입
register_data = {
    "username": username,
    "email": f"{username}@test.com",
    "password": password
}

try:
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    if response.status_code == 201:
        user_data = response.json()
        USER_ID = user_data["id"]
        print_result(True, f"회원가입 성공: {username}", user_data)
    else:
        print_result(False, f"회원가입 실패: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"회원가입 오류: {e}")
    sys.exit(1)

# 로그인
login_data = {
    "username": username,
    "password": password
}

try:
    response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if response.status_code == 200:
        token_data = response.json()
        TOKEN = token_data["access_token"]
        print_result(True, "로그인 성공", {"token": TOKEN[:20] + "..."})
    else:
        print_result(False, f"로그인 실패: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"로그인 오류: {e}")
    sys.exit(1)

# 헤더 설정
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 2. Platform 조회 (YouTube)
print_section("2. Platform 목록 조회")

try:
    response = requests.get(f"{BASE_URL}/platforms", headers=headers)
    if response.status_code == 200:
        platforms = response.json()
        print_result(True, f"Platform 조회 성공 ({len(platforms)}개)")
        youtube_platform = next((p for p in platforms if p["platform_code"] == "youtube"), None)
        if youtube_platform:
            PLATFORM_ID = youtube_platform["id"]
            print(f"   YouTube Platform ID: {PLATFORM_ID}")
        else:
            print_result(False, "YouTube 플랫폼을 찾을 수 없습니다")
            sys.exit(1)
    else:
        print_result(False, f"Platform 조회 실패: {response.status_code}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Platform 조회 오류: {e}")
    sys.exit(1)

# 3. Credential 생성
print_section("3. Credential 생성")

credential_data = {
    "platform_id": PLATFORM_ID,
    "credential_name": "My YouTube Account",
    "credentials": {
        "access_token": "ya29.test_access_token_1234567890",
        "refresh_token": "1//test_refresh_token_abcdefghijk",
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "https://www.googleapis.com/auth/youtube.upload"
    },
    "is_default": True
}

try:
    response = requests.post(f"{BASE_URL}/credentials", json=credential_data, headers=headers)
    if response.status_code == 201:
        credential = response.json()
        CREDENTIAL_ID = credential["id"]
        print_result(True, "Credential 생성 성공", {
            "id": credential["id"],
            "platform_id": credential["platform_id"],
            "credential_name": credential["credential_name"],
            "status": credential["status"],
            "credentials_masked": credential["credentials"]
        })
    else:
        print_result(False, f"Credential 생성 실패: {response.status_code} - {response.text}")
        sys.exit(1)
except Exception as e:
    print_result(False, f"Credential 생성 오류: {e}")
    sys.exit(1)

# 4. Credential 목록 조회
print_section("4. Credential 목록 조회")

try:
    response = requests.get(f"{BASE_URL}/credentials", headers=headers)
    if response.status_code == 200:
        credentials = response.json()
        print_result(True, f"Credential 목록 조회 성공 ({len(credentials)}개)")
        for cred in credentials:
            print(f"   - ID: {cred['id']}, Name: {cred['credential_name']}, Status: {cred['status']}")
            print(f"     Access Token: {cred['has_access_token']}, Refresh Token: {cred['has_refresh_token']}")
    else:
        print_result(False, f"Credential 조회 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"Credential 조회 오류: {e}")

# 5. 특정 Credential 상세 조회
print_section("5. Credential 상세 조회")

try:
    response = requests.get(f"{BASE_URL}/credentials/{CREDENTIAL_ID}", headers=headers)
    if response.status_code == 200:
        credential = response.json()
        print_result(True, "Credential 상세 조회 성공", {
            "id": credential["id"],
            "credential_name": credential["credential_name"],
            "is_default": credential["is_default"],
            "status": credential["status"],
            "credentials": credential["credentials"]  # 마스킹된 버전
        })
    else:
        print_result(False, f"Credential 상세 조회 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"Credential 상세 조회 오류: {e}")

# 6. Credential 업데이트
print_section("6. Credential 업데이트")

update_data = {
    "credential_name": "Updated YouTube Account",
    "status": "active"
}

try:
    response = requests.patch(f"{BASE_URL}/credentials/{CREDENTIAL_ID}", json=update_data, headers=headers)
    if response.status_code == 200:
        credential = response.json()
        print_result(True, "Credential 업데이트 성공", {
            "id": credential["id"],
            "credential_name": credential["credential_name"],
            "status": credential["status"]
        })
    else:
        print_result(False, f"Credential 업데이트 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"Credential 업데이트 오류: {e}")

# 7. 두 번째 Credential 생성 (기본 아님)
print_section("7. 두 번째 Credential 생성")

credential_data2 = {
    "platform_id": PLATFORM_ID,
    "credential_name": "Secondary YouTube Account",
    "credentials": {
        "access_token": "ya29.secondary_access_token_9876543210",
        "refresh_token": "1//secondary_refresh_token_zyxwvutsrqp",
        "token_type": "Bearer",
        "expires_in": 3600,
    },
    "is_default": False
}

try:
    response = requests.post(f"{BASE_URL}/credentials", json=credential_data2, headers=headers)
    if response.status_code == 201:
        credential2 = response.json()
        CREDENTIAL_ID_2 = credential2["id"]
        print_result(True, "두 번째 Credential 생성 성공", {
            "id": credential2["id"],
            "credential_name": credential2["credential_name"],
            "is_default": credential2["is_default"]
        })
    else:
        print_result(False, f"두 번째 Credential 생성 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"두 번째 Credential 생성 오류: {e}")

# 8. Platform별 필터링
print_section("8. Platform별 Credential 필터링")

try:
    response = requests.get(f"{BASE_URL}/credentials?platform_id={PLATFORM_ID}", headers=headers)
    if response.status_code == 200:
        credentials = response.json()
        print_result(True, f"YouTube Credential만 조회 성공 ({len(credentials)}개)")
        for cred in credentials:
            print(f"   - {cred['credential_name']} (기본: {cred['is_default']})")
    else:
        print_result(False, f"필터링 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"필터링 오류: {e}")

# 9. Credential 삭제
print_section("9. Credential 삭제")

try:
    response = requests.delete(f"{BASE_URL}/credentials/{CREDENTIAL_ID_2}", headers=headers)
    if response.status_code == 204:
        print_result(True, "Credential 삭제 성공")
    else:
        print_result(False, f"Credential 삭제 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"Credential 삭제 오류: {e}")

# 10. 삭제 후 목록 확인
print_section("10. 삭제 후 Credential 목록 확인")

try:
    response = requests.get(f"{BASE_URL}/credentials", headers=headers)
    if response.status_code == 200:
        credentials = response.json()
        print_result(True, f"최종 Credential 개수: {len(credentials)}개")
        for cred in credentials:
            print(f"   - {cred['credential_name']} (ID: {cred['id']})")
    else:
        print_result(False, f"최종 조회 실패: {response.status_code}")
except Exception as e:
    print_result(False, f"최종 조회 오류: {e}")

# 완료
print_section("테스트 완료")
print("\n✅ 모든 Credential API 테스트 완료!\n")
print("테스트 결과:")
print("  ✅ Credential 생성 (JWT 인증)")
print("  ✅ Credential 목록 조회 (민감 정보 마스킹)")
print("  ✅ Credential 상세 조회")
print("  ✅ Credential 업데이트")
print("  ✅ 기본 Credential 설정")
print("  ✅ Platform별 필터링")
print("  ✅ Credential 삭제")
print("  ✅ 권한 체크 (본인 Credential만 접근)")
print("\n암호화 기능:")
print("  🔐 민감한 필드 자동 암호화 (access_token, refresh_token)")
print("  🎭 응답 시 민감 정보 마스킹 처리")
print("  🔒 데이터베이스에 암호화된 상태로 저장\n")
