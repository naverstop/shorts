"""
Platform Credential API Routes
플랫폼 자격증명 관리 엔드포인트
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.platform import UserPlatformCredential, Platform
from app.schemas import (
    CredentialCreate,
    CredentialUpdate,
    CredentialResponse,
    CredentialResponseMasked,
    OAuth2AuthorizationRequest,
    OAuth2AuthorizationResponse,
    OAuth2CallbackRequest,
)
from app.utils.crypto import encrypt_dict_for_db, decrypt_dict_from_db
from app.utils.youtube_oauth import (
    create_authorization_url,
    verify_state,
    exchange_code_for_tokens,
    refresh_access_token,
    get_channel_info,
)
from app.models.channel import Channel


router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])


def mask_sensitive_fields(credentials: dict) -> dict:
    """
    민감한 필드를 마스킹 처리
    """
    masked = credentials.copy()
    sensitive_fields = ["access_token", "refresh_token", "api_key", "api_secret", "client_secret", "password"]
    
    for field in sensitive_fields:
        if field in masked and masked[field]:
            value = str(masked[field])
            if len(value) > 8:
                masked[field] = value[:4] + "****" + value[-4:]
            else:
                masked[field] = "****"
    
    return masked


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(
    credential_data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    새로운 Platform Credential 생성
    
    - **platform_id**: 플랫폼 ID
    - **credential_name**: 자격증명 이름 (선택)
    - **credentials**: 자격증명 데이터 (JSON)
    - **is_default**: 기본 자격증명으로 설정 여부
    """
    # Platform 존재 확인
    platform_result = await db.execute(
        select(Platform).where(Platform.id == credential_data.platform_id)
    )
    platform = platform_result.scalar_one_or_none()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform ID {credential_data.platform_id} not found"
        )
    
    # 같은 이름의 자격증명이 이미 있는지 확인
    if credential_data.credential_name:
        existing_result = await db.execute(
            select(UserPlatformCredential).where(
                and_(
                    UserPlatformCredential.user_id == current_user.id,
                    UserPlatformCredential.platform_id == credential_data.platform_id,
                    UserPlatformCredential.credential_name == credential_data.credential_name
                )
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Credential with name '{credential_data.credential_name}' already exists for this platform"
            )
    
    # 기본 자격증명으로 설정 시, 기존 기본 자격증명 해제
    if credential_data.is_default:
        await db.execute(
            select(UserPlatformCredential).where(
                and_(
                    UserPlatformCredential.user_id == current_user.id,
                    UserPlatformCredential.platform_id == credential_data.platform_id,
                    UserPlatformCredential.is_default == True
                )
            )
        )
        result = await db.execute(
            select(UserPlatformCredential).where(
                and_(
                    UserPlatformCredential.user_id == current_user.id,
                    UserPlatformCredential.platform_id == credential_data.platform_id,
                    UserPlatformCredential.is_default == True
                )
            )
        )
        existing_default = result.scalar_one_or_none()
        if existing_default:
            existing_default.is_default = False
    
    # 자격증명 암호화
    encrypted_credentials = encrypt_dict_for_db(credential_data.credentials)
    
    # 새 자격증명 생성
    new_credential = UserPlatformCredential(
        user_id=current_user.id,
        platform_id=credential_data.platform_id,
        credential_name=credential_data.credential_name,
        credentials=encrypted_credentials,
        is_default=credential_data.is_default,
        status="active"
    )
    
    db.add(new_credential)
    await db.commit()
    await db.refresh(new_credential)
    
    # 응답 데이터 준비 (민감 정보 마스킹)
    response_data = CredentialResponse.model_validate(new_credential)
    response_data.credentials = mask_sensitive_fields(new_credential.credentials)
    
    return response_data


@router.get("", response_model=List[CredentialResponseMasked])
async def list_credentials(
    platform_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 Credential 목록 조회
    
    - **platform_id**: 특정 플랫폼의 자격증명만 조회 (선택)
    """
    query = select(UserPlatformCredential).where(
        UserPlatformCredential.user_id == current_user.id
    )
    
    if platform_id:
        query = query.where(UserPlatformCredential.platform_id == platform_id)
    
    query = query.order_by(UserPlatformCredential.created_at.desc())
    
    result = await db.execute(query)
    credentials = result.scalars().all()
    
    # 민감 정보 제외한 응답
    response_list = []
    for cred in credentials:
        response_list.append(
            CredentialResponseMasked(
                id=cred.id,
                user_id=cred.user_id,
                platform_id=cred.platform_id,
                credential_name=cred.credential_name,
                is_default=cred.is_default,
                status=cred.status,
                last_validated=cred.last_validated,
                created_at=cred.created_at,
                updated_at=cred.updated_at,
                has_access_token="access_token" in cred.credentials,
                has_refresh_token="refresh_token" in cred.credentials,
            )
        )
    
    return response_list


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    특정 Credential 상세 조회
    """
    result = await db.execute(
        select(UserPlatformCredential).where(
            and_(
                UserPlatformCredential.id == credential_id,
                UserPlatformCredential.user_id == current_user.id
            )
        )
    )
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential ID {credential_id} not found"
        )
    
    # 응답 데이터 준비 (민감 정보 마스킹)
    response_data = CredentialResponse.model_validate(credential)
    response_data.credentials = mask_sensitive_fields(credential.credentials)
    
    return response_data


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(
    credential_id: int,
    credential_data: CredentialUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Credential 업데이트
    """
    # 권한 확인
    result = await db.execute(
        select(UserPlatformCredential).where(
            and_(
                UserPlatformCredential.id == credential_id,
                UserPlatformCredential.user_id == current_user.id
            )
        )
    )
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential ID {credential_id} not found"
        )
    
    # 업데이트
    update_data = credential_data.model_dump(exclude_unset=True)
    
    if "credentials" in update_data:
        update_data["credentials"] = encrypt_dict_for_db(update_data["credentials"])
    
    if "is_default" in update_data and update_data["is_default"]:
        # 기존 기본 자격증명 해제
        result = await db.execute(
            select(UserPlatformCredential).where(
                and_(
                    UserPlatformCredential.user_id == current_user.id,
                    UserPlatformCredential.platform_id == credential.platform_id,
                    UserPlatformCredential.is_default == True,
                    UserPlatformCredential.id != credential_id
                )
            )
        )
        existing_default = result.scalar_one_or_none()
        if existing_default:
            existing_default.is_default = False
    
    for key, value in update_data.items():
        setattr(credential, key, value)
    
    credential.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(credential)
    
    # 응답 데이터 준비 (민감 정보 마스킹)
    response_data = CredentialResponse.model_validate(credential)
    response_data.credentials = mask_sensitive_fields(credential.credentials)
    
    return response_data


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Credential 삭제
    """
    # 권한 확인
    result = await db.execute(
        select(UserPlatformCredential).where(
            and_(
                UserPlatformCredential.id == credential_id,
                UserPlatformCredential.user_id == current_user.id
            )
        )
    )
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential ID {credential_id} not found"
        )
    
    await db.delete(credential)
    await db.commit()
    
    return None


# ==================== OAuth2 Flow ====================

@router.post("/oauth/youtube/authorize", response_model=OAuth2AuthorizationResponse)
async def start_youtube_oauth(
    request_data: OAuth2AuthorizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    YouTube OAuth2 인증 시작
    
    사용자를 YouTube 로그인 페이지로 리디렉션할 URL 반환
    
    - **platform_id**: 플랫폼 ID (YouTube = 1)
    - **redirect_uri**: 인증 완료 후 돌아올 URI
    """
    # Platform 존재 확인
    platform_result = await db.execute(
        select(Platform).where(Platform.id == request_data.platform_id)
    )
    platform = platform_result.scalar_one_or_none()
    
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform ID {request_data.platform_id} not found"
        )
    
    if platform.platform_code != "youtube":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint only supports YouTube OAuth2"
        )
    
    # Authorization URL 생성
    try:
        auth_url, state = create_authorization_url(
            redirect_uri=request_data.redirect_uri,
            user_id=current_user.id
        )
        
        return OAuth2AuthorizationResponse(
            authorization_url=auth_url,
            state=state
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create authorization URL: {str(e)}"
        )


@router.post("/oauth/youtube/callback", response_model=CredentialResponse)
async def youtube_oauth_callback(
    callback_data: OAuth2CallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    YouTube OAuth2 콜백 처리
    
    Authorization Code를 Access Token으로 교환하고 Credential 생성
    
    - **code**: Authorization Code
    - **state**: CSRF 검증용 state
    - **platform_id**: 플랫폼 ID
    """
    # State 검증
    state_data = verify_state(callback_data.state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state parameter"
        )
    
    user_id = state_data["user_id"]
    redirect_uri = state_data["redirect_uri"]
    
    # 사용자 확인
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Platform 확인
    platform_result = await db.execute(
        select(Platform).where(Platform.id == callback_data.platform_id)
    )
    platform = platform_result.scalar_one_or_none()
    
    if not platform or platform.platform_code != "youtube":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="YouTube platform not found"
        )
    
    # Authorization Code를 토큰으로 교환
    try:
        token_info = exchange_code_for_tokens(
            code=callback_data.code,
            redirect_uri=redirect_uri
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code for tokens: {str(e)}"
        )
    
    # 채널 정보 가져오기
    channel_info = get_channel_info(token_info["access_token"])
    
    if not channel_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve YouTube channel information"
        )
    
    # Credential 이름 생성
    credential_name = f"{channel_info['channel_name']} ({channel_info['channel_id'][:8]}...)"
    
    # 기존 기본 Credential 해제
    await db.execute(
        select(UserPlatformCredential).where(
            and_(
                UserPlatformCredential.user_id == user_id,
                UserPlatformCredential.platform_id == platform.id,
                UserPlatformCredential.is_default == True
            )
        )
    )
    result = await db.execute(
        select(UserPlatformCredential).where(
            and_(
                UserPlatformCredential.user_id == user_id,
                UserPlatformCredential.platform_id == platform.id,
                UserPlatformCredential.is_default == True
            )
        )
    )
    existing_default = result.scalar_one_or_none()
    if existing_default:
        existing_default.is_default = False
    
    # Credential 데이터 준비 및 암호화
    credential_data = {
        "access_token": token_info["access_token"],
        "refresh_token": token_info["refresh_token"],
        "token_uri": token_info["token_uri"],
        "client_id": token_info["client_id"],
        "client_secret": token_info["client_secret"],
        "scopes": token_info["scopes"],
        "expiry": token_info["expiry"],
    }
    
    encrypted_credentials = encrypt_dict_for_db(credential_data)
    
    # Credential 생성
    new_credential = UserPlatformCredential(
        user_id=user_id,
        platform_id=platform.id,
        credential_name=credential_name,
        credentials=encrypted_credentials,
        is_default=True,
        status="active",
        last_validated=datetime.utcnow()
    )
    
    db.add(new_credential)
    await db.commit()
    await db.refresh(new_credential)
    
    # Channel 자동 생성
    # 같은 channel_id가 이미 있는지 확인
    channel_result = await db.execute(
        select(Channel).where(
            and_(
                Channel.user_credential_id == new_credential.id,
                Channel.channel_identifier == channel_info["channel_id"]
            )
        )
    )
    existing_channel = channel_result.scalar_one_or_none()
    
    if not existing_channel:
        new_channel = Channel(
            user_credential_id=new_credential.id,
            channel_name=channel_info["channel_name"],
            channel_identifier=channel_info["channel_id"],
            channel_url=f"https://www.youtube.com/channel/{channel_info['channel_id']}",
            is_active=True,
            status="active"
        )
        db.add(new_channel)
        await db.commit()
    
    # 응답 데이터 준비 (민감 정보 마스킹)
    response_data = CredentialResponse.model_validate(new_credential)
    response_data.credentials = mask_sensitive_fields(new_credential.credentials)
    
    return response_data


@router.post("/oauth/youtube/refresh/{credential_id}", response_model=CredentialResponse)
async def refresh_youtube_token(
    credential_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    YouTube Access Token 갱신
    
    Refresh Token을 사용하여 새 Access Token 발급
    """
    # Credential 조회 및 권한 확인
    result = await db.execute(
        select(UserPlatformCredential).where(
            and_(
                UserPlatformCredential.id == credential_id,
                UserPlatformCredential.user_id == current_user.id
            )
        )
    )
    credential = result.scalar_one_or_none()
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credential ID {credential_id} not found"
        )
    
    # Platform 확인
    platform_result = await db.execute(
        select(Platform).where(Platform.id == credential.platform_id)
    )
    platform = platform_result.scalar_one_or_none()
    
    if not platform or platform.platform_code != "youtube":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This credential is not for YouTube"
        )
    
    # 기존 자격증명에서 refresh_token 추출
    creds = credential.credentials
    
    if "refresh_token" not in creds or not creds["refresh_token"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No refresh token available for this credential"
        )
    
    # 토큰 갱신
    try:
        # 복호화된 값 사용
        from app.utils.crypto import decrypt_dict_from_db
        decrypted_creds = decrypt_dict_from_db(creds)
        
        new_token_info = refresh_access_token(
            refresh_token=decrypted_creds["refresh_token"],
            client_id=decrypted_creds["client_id"],
            client_secret=decrypted_creds["client_secret"]
        )
    except Exception as e:
        # 갱신 실패 시 상태 업데이트
        credential.status = "expired"
        await db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to refresh token: {str(e)}"
        )
    
    # Credential 업데이트
    creds["access_token"] = new_token_info["access_token"]
    creds["expiry"] = new_token_info["expiry"]
    if new_token_info.get("refresh_token"):
        creds["refresh_token"] = new_token_info["refresh_token"]
    
    # 재암호화
    credential.credentials = encrypt_dict_for_db(creds)
    credential.status = "active"
    credential.last_validated = datetime.utcnow()
    credential.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(credential)
    
    # 응답 데이터 준비 (민감 정보 마스킹)
    response_data = CredentialResponse.model_validate(credential)
    response_data.credentials = mask_sensitive_fields(credential.credentials)
    
    return response_data
