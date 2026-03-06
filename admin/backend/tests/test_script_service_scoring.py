"""
Tests for ScriptService scoring logic
"""
from app.services.script_service import ScriptService


def test_quality_score_with_well_structured_script():
    script_data = {
        "title": "AI 트렌드 핵심 정리",
        "hook": "이 10초가 조회수를 바꿉니다!",
        "body": "핵심 내용과 사례를 빠르게 전달합니다.",
        "cta": "댓글로 의견을 남겨주세요.",
        "full_script": "이 10초가 조회수를 바꿉니다. 핵심 내용과 사례를 빠르게 전달합니다. 댓글로 의견을 남겨주세요.",
    }

    score = ScriptService._calculate_quality_score(script_data)

    assert score >= 55
    assert score <= 100


def test_viral_potential_with_trend_score():
    script_data = {
        "title": "왜 이 영상이 터졌을까?",
        "hook": "충격적인 반전이 있습니다!",
        "cta": "좋아요와 공유 부탁드려요!",
    }

    score = ScriptService._calculate_viral_potential(script_data, trend_score=80.0)

    assert score > 70
    assert score <= 100
