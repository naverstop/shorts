"""
암호화 유틸리티
Platform Credential 암호화/복호화 기능
"""
import os
import json
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64


# 환경 변수에서 암호화 키 가져오기 (없으면 기본값 사용)
SECRET_KEY = os.getenv("ENCRYPTION_SECRET_KEY", "shorts-admin-secret-key-2026")
SALT = b"shorts_admin_salt_2026"  # 고정된 salt (프로덕션에서는 환경 변수 사용)


def _get_fernet_key() -> bytes:
    """
    SECRET_KEY와 SALT로부터 Fernet 키 생성
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(SECRET_KEY.encode()))
    return key


def encrypt_credentials(credentials: dict) -> str:
    """
    자격증명 딕셔너리를 암호화하여 문자열로 반환
    
    Args:
        credentials: 암호화할 자격증명 딕셔너리
        
    Returns:
        암호화된 문자열
    """
    try:
        fernet = Fernet(_get_fernet_key())
        json_str = json.dumps(credentials)
        encrypted_bytes = fernet.encrypt(json_str.encode())
        return encrypted_bytes.decode()
    except Exception as e:
        raise ValueError(f"자격증명 암호화 실패: {str(e)}")


def decrypt_credentials(encrypted_credentials: str) -> dict:
    """
    암호화된 자격증명 문자열을 복호화하여 딕셔너리로 반환
    
    Args:
        encrypted_credentials: 암호화된 자격증명 문자열
        
    Returns:
        복호화된 자격증명 딕셔너리
    """
    try:
        fernet = Fernet(_get_fernet_key())
        decrypted_bytes = fernet.decrypt(encrypted_credentials.encode())
        return json.loads(decrypted_bytes.decode())
    except Exception as e:
        raise ValueError(f"자격증명 복호화 실패: {str(e)}")


def encrypt_dict_for_db(credentials: dict) -> dict:
    """
    데이터베이스 저장을 위해 민감한 필드만 암호화
    
    Args:
        credentials: 원본 자격증명 딕셔너리
        
    Returns:
        민감한 필드가 암호화된 딕셔너리
    """
    # 민감한 필드 목록
    sensitive_fields = [
        "access_token",
        "refresh_token",
        "api_key",
        "api_secret",
        "client_secret",
        "password",
        "private_key",
    ]
    
    result = credentials.copy()
    
    for field in sensitive_fields:
        if field in result and result[field]:
            try:
                result[field] = encrypt_credentials({field: result[field]})
            except Exception:
                pass  # 암호화 실패 시 원본 유지
    
    return result


def decrypt_dict_from_db(credentials: dict) -> dict:
    """
    데이터베이스에서 가져온 자격증명의 민감한 필드 복호화
    
    Args:
        credentials: 암호화된 필드를 포함한 자격증명 딕셔너리
        
    Returns:
        모든 필드가 복호화된 딕셔너리
    """
    # 민감한 필드 목록
    sensitive_fields = [
        "access_token",
        "refresh_token",
        "api_key",
        "api_secret",
        "client_secret",
        "password",
        "private_key",
    ]
    
    result = credentials.copy()
    
    for field in sensitive_fields:
        if field in result and result[field]:
            try:
                decrypted = decrypt_credentials(result[field])
                result[field] = decrypted.get(field, result[field])
            except Exception:
                pass  # 복호화 실패 시 원본 유지 (암호화되지 않은 경우)
    
    return result
