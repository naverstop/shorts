"""
Platform Credential Schemas
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime


class CredentialBase(BaseModel):
    """Credential 기본 스키마"""
    platform_id: int = Field(..., description="플랫폼 ID")
    credential_name: Optional[str] = Field(None, max_length=100, description="자격증명 이름")
    credentials: Dict[str, Any] = Field(..., description="자격증명 데이터 (JSON)")
    is_default: bool = Field(default=False, description="기본 자격증명 여부")


class CredentialCreate(CredentialBase):
    """Credential 생성 스키마"""
    pass


class CredentialUpdate(BaseModel):
    """Credential 업데이트 스키마"""
    credential_name: Optional[str] = Field(None, max_length=100)
    credentials: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None
    status: Optional[str] = Field(None, pattern="^(active|expired|invalid)$")


class CredentialResponse(BaseModel):
    """Credential 응답 스키마"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    platform_id: int
    credential_name: Optional[str]
    credentials: Dict[str, Any]  # 민감한 정보는 마스킹됨
    is_default: bool
    status: str
    last_validated: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CredentialResponseMasked(BaseModel):
    """Credential 응답 스키마 (민감 정보 마스킹)"""
    model_config = ConfigDict(from_attributes=True)
    
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


class CredentialValidateRequest(BaseModel):
    """Credential 검증 요청 스키마"""
    credential_id: int = Field(..., description="검증할 Credential ID")


class CredentialValidateResponse(BaseModel):
    """Credential 검증 응답 스키마"""
    credential_id: int
    is_valid: bool
    message: str
    validated_at: datetime


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
