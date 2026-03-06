"""
Pydantic Schemas for API
"""
from pydantic import BaseModel, Field, field_serializer
from typing import Optional, List, Any
from datetime import datetime


# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# Base Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=72)


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentBase(BaseModel):
    device_name: str
    sim_carrier: Optional[str] = None
    android_version: Optional[str] = None


class AgentCreate(AgentBase):
    device_id: str
    apk_version: Optional[str] = None


class AgentUpdate(BaseModel):
    device_name: Optional[str] = None
    sim_carrier: Optional[str] = None
    android_version: Optional[str] = None
    apk_version: Optional[str] = None
    status: Optional[str] = Field(None, pattern='^(idle|processing|offline|banned)$')
    disk_usage_percent: Optional[int] = Field(None, ge=0, le=100)


class AgentHeartbeat(BaseModel):
    disk_usage_percent: Optional[int] = Field(None, ge=0, le=100)
    apk_version: Optional[str] = None
    android_version: Optional[str] = None


class AgentResponse(AgentBase):
    id: int
    user_id: int
    device_id: str
    api_key: str
    status: str
    last_heartbeat: Optional[datetime] = None
    ip_address: Optional[Any] = None  # Allow IPv4Address or str
    disk_usage_percent: int
    last_disk_cleanup: Optional[datetime] = None
    apk_version: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @field_serializer('ip_address')
    def serialize_ip(self, value: Any, _info):
        """Convert IPv4Address to string"""
        if value is None:
            return None
        return str(value)
    
    class Config:
        from_attributes = True


class AgentStats(BaseModel):
    total: int
    by_status: dict
    online_count: int  # heartbeat within last 5 minutes
    offline_count: int


class JobBase(BaseModel):
    title: str
    script: str
    source_language: str = "ko"
    target_languages: List[str] = ["ko"]


class JobCreate(JobBase):
    platform_id: int = Field(..., description="Target platform ID for upload")
    job_metadata: Optional[dict] = None
    priority: int = Field(default=5, ge=1, le=10)


class JobUpdate(BaseModel):
    title: Optional[str] = None
    script: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = Field(None, pattern='^(pending|assigned|rendering|uploading|completed|failed)$')


class JobAssign(BaseModel):
    agent_id: int


class JobStatusUpdate(BaseModel):
    status: str = Field(..., pattern='^(assigned|rendering|uploading|completed|failed)$')
    error_message: Optional[str] = None
    video_path: Optional[str] = None
    video_url: Optional[str] = None


class JobPublishYoutubeRequest(BaseModel):
    credential_id: Optional[int] = None
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[List[str]] = None
    privacy_status: str = Field(default="private", pattern='^(private|public|unlisted)$')


class JobPublishYoutubeResponse(BaseModel):
    status: str
    platform: str
    job_id: int
    video_id: Optional[str] = None
    video_url: Optional[str] = None
    credential_id: int


class JobPublishTiktokRequest(BaseModel):
    credential_id: Optional[int] = None
    caption: Optional[str] = Field(None, max_length=2200)
    headless: bool = True


class JobPublishTiktokResponse(BaseModel):
    status: str
    platform: str
    job_id: int
    video_url: Optional[str] = None
    credential_id: int


class JobResponse(JobBase):
    id: int
    user_id: int
    agent_id: Optional[int] = None
    target_platform_id: int
    status: str
    priority: int
    retry_count: int
    job_metadata: Optional[dict] = None
    error_message: Optional[str] = None
    created_at: datetime
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class JobStats(BaseModel):
    total: int
    by_status: dict
    pending_count: int
    processing_count: int  # assigned + rendering + uploading
    completed_count: int
    failed_count: int
    avg_processing_time: Optional[float] = None  # in seconds


class PlatformResponse(BaseModel):
    id: int
    platform_code: str
    platform_name: str
    is_active: bool
    auth_type: str
    api_endpoint: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlatformDetailResponse(PlatformResponse):
    required_fields: Optional[dict] = None
    documentation_url: Optional[str] = None


class LanguageResponse(BaseModel):
    id: int
    language_code: str
    language_name: str
    native_name: str
    tts_voice_code: Optional[str] = None
    is_active: bool
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    status: str
    database: str
    redis: str
    services: dict


# Platform Credential Schemas
class CredentialBase(BaseModel):
    """Credential 기본 스키마"""
    platform_id: int = Field(..., description="플랫폼 ID")
    credential_name: Optional[str] = Field(None, max_length=100, description="자격증명 이름")
    credentials: dict = Field(..., description="자격증명 데이터 (JSON)")
    is_default: bool = Field(default=False, description="기본 자격증명 여부")


class CredentialCreate(CredentialBase):
    """Credential 생성 스키마"""
    pass


class CredentialUpdate(BaseModel):
    """Credential 업데이트 스키마"""
    credential_name: Optional[str] = Field(None, max_length=100)
    credentials: Optional[dict] = None
    is_default: Optional[bool] = None
    status: Optional[str] = Field(None, pattern="^(active|expired|invalid)$")


class CredentialResponse(BaseModel):
    """Credential 응답 스키마"""
    id: int
    user_id: int
    platform_id: int
    credential_name: Optional[str]
    credentials: dict  # 민감한 정보는 마스킹됨
    is_default: bool
    status: str
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CredentialResponseMasked(BaseModel):
    """Credential 응답 스키마 (민감 정보 마스킹)"""
    id: int
    user_id: int
    platform_id: int
    credential_name: Optional[str]
    is_default: bool
    status: str
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    has_access_token: bool = Field(description="Access Token 존재 여부")
    has_refresh_token: bool = Field(description="Refresh Token 존재 여부")
    
    class Config:
        from_attributes = True


class OAuth2AuthorizationRequest(BaseModel):
    """OAuth2 인증 시작 요청"""
    platform_id: int = Field(..., description="플랫폼 ID")
    redirect_uri: str = Field(..., description="콜백 URI")
    state: Optional[str] = Field(None, description="CSRF 방지용 state")


class OAuth2AuthorizationResponse(BaseModel):
    """OAuth2 인증 시작 응답"""
    authorization_url: str = Field(..., description="사용자가 방문할 인증 URL")
    state: str = Field(..., description="CSRF 검증용 state")


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 콜백 요청"""
    code: str = Field(..., description="Authorization Code")
    state: str = Field(..., description="CSRF 검증용 state")
    platform_id: int = Field(..., description="플랫폼 ID")


class OAuth2TokenResponse(BaseModel):
    """OAuth2 토큰 교환 응답"""
    credential_id: int
    access_token: str
    refresh_token: Optional[str]
    expires_in: Optional[int]
    token_type: str
    scope: Optional[str]


# Upload Quota Schemas
class UploadQuotaBase(BaseModel):
    """업로드 할당량 기본 스키마"""
    daily_limit: int = Field(0, ge=0, description="일일 업로드 제한 (0=무제한)")
    weekly_limit: int = Field(0, ge=0, description="주간 업로드 제한 (0=무제한)")
    monthly_limit: int = Field(0, ge=0, description="월간 업로드 제한 (0=무제한)")


class UploadQuotaCreate(UploadQuotaBase):
    """업로드 할당량 생성 요청"""
    platform_id: int = Field(..., description="플랫폼 ID")


class UploadQuotaUpdate(BaseModel):
    """업로드 할당량 수정 요청"""
    daily_limit: Optional[int] = Field(None, ge=0, description="일일 업로드 제한")
    weekly_limit: Optional[int] = Field(None, ge=0, description="주간 업로드 제한")
    monthly_limit: Optional[int] = Field(None, ge=0, description="월간 업로드 제한")


class UploadQuotaResponse(UploadQuotaBase):
    """업로드 할당량 응답"""
    id: int
    user_id: int
    platform_id: int
    
    # 사용량
    used_today: int
    used_week: int
    used_month: int
    
    # 남은 할당량 (-1 = 무제한)
    remaining_daily: int = Field(description="남은 일일 할당량")
    remaining_weekly: int = Field(description="남은 주간 할당량")
    remaining_monthly: int = Field(description="남은 월간 할당량")
    
    # 초과 여부
    is_quota_exceeded: bool = Field(description="할당량 초과 여부")
    
    # 리셋 시간
    last_daily_reset: datetime
    last_weekly_reset: datetime
    last_monthly_reset: datetime
    
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UploadQuotaCheck(BaseModel):
    """업로드 가능 여부 체크 응답"""
    can_upload: bool = Field(description="업로드 가능 여부")
    reason: Optional[str] = Field(None, description="불가능한 경우 이유")
    remaining_daily: int = Field(description="남은 일일 할당량 (-1=무제한)")
    remaining_weekly: int = Field(description="남은 주간 할당량 (-1=무제한)")
    remaining_monthly: int = Field(description="남은 월간 할당량 (-1=무제한)")
    next_reset: Optional[datetime] = Field(None, description="다음 리셋 시간")


class UploadQuotaStats(BaseModel):
    """전체 할당량 통계"""
    total_quotas: int = Field(description="총 할당량 설정 수")
    exceeded_count: int = Field(description="초과된 할당량 수")
    platforms: List[dict] = Field(description="플랫폼별 통계")


# ==================== Trend Schemas ====================

class TrendResponse(BaseModel):
    """트렌드 응답"""
    id: int
    source: str
    keyword: str
    topic: Optional[str]
    category: Optional[str]
    trend_score: float
    view_count: int
    video_count: int
    growth_rate: float
    ai_analysis: Optional[dict]
    suggested_tags: Optional[List[str]]
    related_keywords: Optional[List[str]]
    language: str
    region: str
    collected_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrendCollectRequest(BaseModel):
    """트렌드 수집 요청"""
    region_code: str = Field(default="KR", description="지역 코드")
    category_id: Optional[str] = Field(None, description="카테고리 ID")


class TrendSearchRequest(BaseModel):
    """트렌드 검색 요청"""
    query: str = Field(..., description="검색 쿼리")
    source: Optional[str] = Field(None, description="소스 필터 (youtube, tiktok)")


# ==================== Script Schemas ====================

class ScriptGenerateRequest(BaseModel):
    """스크립트 생성 요청"""
    topic: str = Field(..., description="주제/키워드", min_length=1)
    trend_id: Optional[int] = Field(None, description="관련 트렌드 ID")
    target_audience: str = Field(default="20-30대", description="타겟 청중")
    platform: str = Field(default="youtube_shorts", description="플랫폼")
    language: str = Field(default="ko", description="언어")
    duration: int = Field(default=60, description="영상 길이 (초)", ge=15, le=180)


class ScriptResponse(BaseModel):
    """스크립트 응답"""
    id: int
    user_id: int
    trend_id: Optional[int]
    title: str
    content: str
    hook: Optional[str]
    body: Optional[str]
    cta: Optional[str]
    ai_model: Optional[str]
    quality_score: float
    viral_potential: float
    used_count: int
    is_approved: bool
    is_archived: bool
    language: str
    target_platforms: Optional[dict]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ScriptSimilarityResponse(BaseModel):
    """유사 스크립트 응답"""
    id: int
    title: str
    content: str
    user_id: int
    created_at: datetime
    similarity: float = Field(description="유사도 (0.0 ~ 1.0)")
