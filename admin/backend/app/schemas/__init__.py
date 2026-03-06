"""
Pydantic Schemas 패키지
"""
# 상위 디렉토리의 schemas.py에서 기존 스키마 import
import sys
from pathlib import Path

# 상위 디렉토리를 path에 추가
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# 기존 schemas 모듈의 내용을 동적으로 import
import importlib.util
schemas_file = parent_dir / "schemas.py"
spec = importlib.util.spec_from_file_location("original_schemas", schemas_file)
original_schemas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(original_schemas)

# 기존 스키마들을 현재 네임스페이스로 가져오기
Token = original_schemas.Token
TokenData = original_schemas.TokenData
UserBase = original_schemas.UserBase
UserCreate = original_schemas.UserCreate
UserResponse = original_schemas.UserResponse
AgentBase = original_schemas.AgentBase
AgentCreate = original_schemas.AgentCreate
AgentUpdate = original_schemas.AgentUpdate
AgentHeartbeat = original_schemas.AgentHeartbeat
AgentResponse = original_schemas.AgentResponse
AgentStats = original_schemas.AgentStats
JobBase = original_schemas.JobBase
JobCreate = original_schemas.JobCreate
JobUpdate = original_schemas.JobUpdate
JobResponse = original_schemas.JobResponse
JobAssign = original_schemas.JobAssign
JobStatusUpdate = original_schemas.JobStatusUpdate
JobPublishYoutubeRequest = original_schemas.JobPublishYoutubeRequest
JobPublishYoutubeResponse = original_schemas.JobPublishYoutubeResponse
JobPublishTiktokRequest = original_schemas.JobPublishTiktokRequest
JobPublishTiktokResponse = original_schemas.JobPublishTiktokResponse
JobStats = original_schemas.JobStats
PlatformResponse = original_schemas.PlatformResponse
PlatformDetailResponse = original_schemas.PlatformDetailResponse
LanguageResponse = original_schemas.LanguageResponse

# Upload Quota 스키마
UploadQuotaBase = original_schemas.UploadQuotaBase
UploadQuotaCreate = original_schemas.UploadQuotaCreate
UploadQuotaUpdate = original_schemas.UploadQuotaUpdate
UploadQuotaResponse = original_schemas.UploadQuotaResponse
UploadQuotaCheck = original_schemas.UploadQuotaCheck
UploadQuotaStats = original_schemas.UploadQuotaStats

# AI Integration 스키마
TrendResponse = original_schemas.TrendResponse
TrendCollectRequest = original_schemas.TrendCollectRequest
TrendSearchRequest = original_schemas.TrendSearchRequest
ScriptGenerateRequest = original_schemas.ScriptGenerateRequest
ScriptResponse = original_schemas.ScriptResponse
ScriptSimilarityResponse = original_schemas.ScriptSimilarityResponse

# Credential 스키마 import
from app.schemas.credential import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialResponseMasked,
    CredentialValidateRequest,
    CredentialValidateResponse,
    OAuth2AuthorizationRequest,
    OAuth2AuthorizationResponse,
    OAuth2CallbackRequest,
    OAuth2TokenResponse,
)

__all__ = [
    # Auth
    "Token", "TokenData",
    # User
    "UserBase", "UserCreate", "UserResponse",
    # Agent
    "AgentBase", "AgentCreate", "AgentUpdate", "AgentHeartbeat", "AgentResponse", "AgentStats",
    # Job
    "JobBase", "JobCreate", "JobUpdate", "JobResponse", "JobAssign", "JobStatusUpdate", "JobStats",
    "JobPublishYoutubeRequest", "JobPublishYoutubeResponse",
    "JobPublishTiktokRequest", "JobPublishTiktokResponse",
    # Platform
    "PlatformResponse", "PlatformDetailResponse", "LanguageResponse",
    # Credential
    "CredentialCreate",
    "CredentialUpdate",
    "CredentialResponse",
    "CredentialResponseMasked",
    "CredentialValidateRequest",
    "CredentialValidateResponse",
    "OAuth2AuthorizationRequest",
    "OAuth2AuthorizationResponse",
    "OAuth2CallbackRequest",
    "OAuth2TokenResponse",
    # Upload Quota
    "UploadQuotaBase",
    "UploadQuotaCreate",
    "UploadQuotaUpdate",
    "UploadQuotaResponse",
    "UploadQuotaCheck",
    "UploadQuotaStats",
    # AI Integration
    "TrendResponse",
    "TrendCollectRequest",
    "TrendSearchRequest",
    "ScriptGenerateRequest",
    "ScriptResponse",
    "ScriptSimilarityResponse",
]
