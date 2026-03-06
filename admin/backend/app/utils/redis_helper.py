"""
Redis 유틸리티
State 관리 및 캐싱
"""
import redis
import os
import json
from typing import Optional, Any

# Redis 연결 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis_password_2026")
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Redis 클라이언트 생성
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    password=REDIS_PASSWORD,
    db=REDIS_DB,
    decode_responses=True
)


def set_with_expiry(key: str, value: Any, expiry_seconds: int = 300) -> bool:
    """
    키-값을 Redis에 저장 (만료 시간 설정)
    
    Args:
        key: Redis 키
        value: 저장할 값 (자동으로 JSON 직렬화)
        expiry_seconds: 만료 시간 (초, 기본 5분)
        
    Returns:
        저장 성공 여부
    """
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        redis_client.setex(key, expiry_seconds, value)
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False


def get_value(key: str) -> Optional[str]:
    """
    Redis에서 값 가져오기
    
    Args:
        key: Redis 키
        
    Returns:
        저장된 값 (없으면 None)
    """
    try:
        return redis_client.get(key)
    except Exception as e:
        print(f"Redis get error: {e}")
        return None


def delete_key(key: str) -> bool:
    """
    Redis 키 삭제
    
    Args:
        key: Redis 키
        
    Returns:
        삭제 성공 여부
    """
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Redis delete error: {e}")
        return False


def get_json(key: str) -> Optional[dict]:
    """
    Redis에서 JSON 값 가져오기
    
    Args:
        key: Redis 키
        
    Returns:
        JSON 파싱된 딕셔너리 (없거나 파싱 실패 시 None)
    """
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Redis get JSON error: {e}")
        return None


def ping() -> bool:
    """
    Redis 연결 상태 확인
    
    Returns:
        연결 성공 여부
    """
    try:
        return redis_client.ping()
    except Exception as e:
        print(f"Redis ping error: {e}")
        return False
