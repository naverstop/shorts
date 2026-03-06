"""
YouTube OAuth2 Helper
YouTube API OAuth2 인증 플로우 헬퍼
"""
import os
import json
import secrets
from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import redis

# YouTube OAuth2 스콥
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
]

# Redis 클라이언트 (state 저장용)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD", "redis_password_2026"),
    db=0,
    decode_responses=True
)


def get_oauth_config() -> Dict[str, Any]:
    """
    YouTube OAuth2 클라이언트 설정 가져오기
    환경 변수 또는 기본값 사용
    """
    # 실제 프로덕션에서는 환경 변수나 설정 파일에서 가져와야 함
    return {
        "web": {
            "client_id": os.getenv(
                "YOUTUBE_CLIENT_ID",
                "YOUR_CLIENT_ID.apps.googleusercontent.com"
            ),
            "client_secret": os.getenv(
                "YOUTUBE_CLIENT_SECRET",
                "YOUR_CLIENT_SECRET"
            ),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [
                os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8001/api/v1/oauth/youtube/callback")
            ],
        }
    }


def create_authorization_url(redirect_uri: str, user_id: int) -> tuple[str, str]:
    """
    OAuth2 인증 URL 생성
    
    Args:
        redirect_uri: 콜백 URI
        user_id: 사용자 ID (state에 포함)
        
    Returns:
        (authorization_url, state)
    """
    # State 생성 (CSRF 방지)
    state = secrets.token_urlsafe(32)
    
    # Redis에 state 저장 (5분 TTL)
    state_key = f"oauth:state:{state}"
    state_data = {
        "user_id": user_id,
        "redirect_uri": redirect_uri
    }
    redis_client.setex(state_key, 300, json.dumps(state_data))  # 5분
    
    # OAuth2 Flow 생성
    config = get_oauth_config()
    flow = Flow.from_client_config(
        config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=redirect_uri
    )
    
    # Authorization URL 생성
    authorization_url, _ = flow.authorization_url(
        access_type="offline",  # refresh token 받기 위해
        include_granted_scopes="true",
        state=state,
        prompt="consent"  # 항상 동의 화면 표시 (refresh token 받기 위해)
    )
    
    return authorization_url, state


def verify_state(state: str) -> Optional[Dict[str, Any]]:
    """
    State 검증 및 데이터 반환
    
    Args:
        state: 검증할 state
        
    Returns:
        state 데이터 (user_id, redirect_uri) 또는 None
    """
    state_key = f"oauth:state:{state}"
    state_data_str = redis_client.get(state_key)
    
    if not state_data_str:
        return None
    
    # state 삭제 (일회용)
    redis_client.delete(state_key)
    
    return json.loads(state_data_str)


def exchange_code_for_tokens(code: str, redirect_uri: str) -> Dict[str, Any]:
    """
    Authorization Code를 Access Token으로 교환
    
    Args:
        code: Authorization Code
        redirect_uri: 콜백 URI (검증용)
        
    Returns:
        토큰 정보 딕셔너리
    """
    config = get_oauth_config()
    flow = Flow.from_client_config(
        config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=redirect_uri
    )
    
    # 토큰 교환
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    
    # 토큰 정보 추출
    token_info = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }
    
    return token_info


def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> Dict[str, Any]:
    """
    Refresh Token으로 새 Access Token 발급
    
    Args:
        refresh_token: Refresh Token
        client_id: OAuth2 Client ID
        client_secret: OAuth2 Client Secret
        
    Returns:
        새 토큰 정보
    """
    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    
    # 토큰 갱신
    request = Request()
    credentials.refresh(request)
    
    # 새 토큰 정보
    token_info = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token or refresh_token,  # 새 refresh token이 없으면 기존 것 사용
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }
    
    return token_info


def get_channel_info(access_token: str) -> Optional[Dict[str, Any]]:
    """
    Access Token으로 YouTube 채널 정보 가져오기
    
    Args:
        access_token: YouTube Access Token
        
    Returns:
        채널 정보 또는 None
    """
    from googleapiclient.discovery import build
    
    try:
        credentials = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=credentials)
        
        # 내 채널 정보 가져오기
        request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            mine=True
        )
        response = request.execute()
        
        if not response.get("items"):
            return None
        
        channel = response["items"][0]
        return {
            "channel_id": channel["id"],
            "channel_name": channel["snippet"]["title"],
            "channel_description": channel["snippet"].get("description", ""),
            "custom_url": channel["snippet"].get("customUrl"),
            "thumbnail_url": channel["snippet"]["thumbnails"]["default"]["url"],
            "subscriber_count": int(channel["statistics"].get("subscriberCount", 0)),
            "video_count": int(channel["statistics"].get("videoCount", 0)),
            "view_count": int(channel["statistics"].get("viewCount", 0)),
        }
    except Exception as e:
        print(f"Failed to get channel info: {e}")
        return None
