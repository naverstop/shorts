"""
Upload Quota API 단위 테스트
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_upload_quotas_unauthorized():
    """인증 없이 할당량 조회 시 401 반환"""
    response = client.get("/api/v1/upload-quotas")
    assert response.status_code == 401


def test_create_upload_quota_unauthorized():
    """인증 없이 할당량 생성 시 401 반환"""
    response = client.post(
        "/api/v1/upload-quotas",
        json={
            "platform_id": 1,
            "daily_limit": 10,
            "weekly_limit": 50,
            "monthly_limit": 200,
        },
    )
    assert response.status_code == 401


def test_delete_upload_quota_unauthorized():
    """인증 없이 할당량 삭제 시 401 반환"""
    response = client.delete("/api/v1/upload-quotas/1")
    assert response.status_code == 401


def test_reset_daily_quotas_unauthorized():
    """인증 없이 일일 할당량 리셋 시 401 반환"""
    response = client.post("/api/v1/upload-quotas/reset/daily")
    assert response.status_code == 401


def test_reset_weekly_quotas_unauthorized():
    """인증 없이 주간 할당량 리셋 시 401 반환"""
    response = client.post("/api/v1/upload-quotas/reset/weekly")
    assert response.status_code == 401


def test_reset_monthly_quotas_unauthorized():
    """인증 없이 월간 할당량 리셋 시 401 반환"""
    response = client.post("/api/v1/upload-quotas/reset/monthly")
    assert response.status_code == 401


def test_upload_quota_endpoints_exist():
    """Upload Quota 엔드포인트들이 존재하는지 확인"""
    # 엔드포인트가 존재하면 401 또는 422 반환, 404가 아님
    response = client.get("/api/v1/upload-quotas")
    assert response.status_code != 404
    
    response = client.post("/api/v1/upload-quotas", json={})
    assert response.status_code != 404
    
    response = client.delete("/api/v1/upload-quotas/1")
    assert response.status_code != 404
    
    response = client.post("/api/v1/upload-quotas/reset/daily")
    assert response.status_code != 404
