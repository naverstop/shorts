# 🔑 API 키 구조 및 분리 관리 가이드

**작성일**: 2026년 3월 2일  
**버전**: 1.0

---

## 📋 목차
1. [개요](#개요)
2. [전체 프로젝트용 API 키](#1-전체-프로젝트용-api-키)
3. [사용자별 API 키](#2-사용자별-api-키)
4. [분리 관리 방식](#3-분리-관리-방식)
5. [보안 체크리스트](#4-보안-체크리스트)

---

## 개요

AI 기반 쇼츠 자동 생성 시스템은 **2가지 레벨의 API 키**를 사용합니다:

### 🌐 레벨 1: 전체 프로젝트용 API 키
- Admin 서버 전역에서 사용
- `.env` 파일에 저장
- AI 콘텐츠 생성, 시스템 인증 담당

### 👥 레벨 2: 사용자별 API 키
- 각 사용자가 개별 등록
- `UserPlatformCredential` 테이블에 **암호화 저장**
- 플랫폼 업로드, 채널 관리 담당

> **⚠️ 핵심**: 이 2가지 레벨은 **반드시 분리**되어야 합니다!

---

## 1. 전체 프로젝트용 API 키

### 📍 저장 위치
`admin/backend/.env` 파일 (Git 제외)

### 🔹 AI 서비스 (콘텐츠 생성용)

#### 1.1 YOUTUBE_API_KEY
```bash
YOUTUBE_API_KEY=AIzaSyD1234567890abcdefghijklmnop
```

| 항목 | 내용 |
|------|------|
| **용도** | YouTube 트렌드 수집, 공개 데이터 조회 |
| **사용처** | `app/services/youtube_client.py` |
| **권한** | **Read-Only** (업로드 권한 없음) |
| **API** | YouTube Data API v3 |
| **발급처** | [Google Cloud Console](https://console.cloud.google.com) |
| **비용** | 무료 (하루 10,000 쿼터, 약 100회 API 호출) |

**주요 메서드**:
```python
async def get_trending_videos(region_code: str = "KR") -> List[Dict]:
    # YouTube 인기 급상승 동영상 조회
```

---

#### 1.2 GEMINI_API_KEY
```bash
GEMINI_API_KEY=AIzaSyA9876543210zyxwvutsrqponmlk
```

| 항목 | 내용 |
|------|------|
| **용도** | 트렌드 분석, 키워드 추출, 시장 분석 |
| **사용처** | `app/services/gemini_client.py` |
| **모델** | Gemini 2.0 Flash |
| **발급처** | [Google AI Studio](https://makersuite.google.com/app/apikey) |
| **비용** | 무료 (일일 1,500 요청, 분당 15 요청) |

**주요 메서드**:
```python
async def analyze_trend(trend_data: Dict) -> Dict:
    # 트렌드 데이터 분석, 키워드 추출
```

---

#### 1.3 ANTHROPIC_API_KEY
```bash
ANTHROPIC_API_KEY=sk-ant-api03-1234567890abcdef
```

| 항목 | 내용 |
|------|------|
| **용도** | 스크립트 생성, 자막 생성 |
| **사용처** | `app/services/claude_client.py` |
| **모델** | Claude 3.5 Sonnet |
| **발급처** | [Anthropic Console](https://console.anthropic.com/) |
| **비용** | $5 무료 크레딧, 이후 Input $3/1M tokens, Output $15/1M tokens |

**주요 메서드**:
```python
async def generate_script(prompt: str, language: str) -> Dict:
    # 쇼츠 스크립트 생성
```

---

#### 1.4 OPENAI_API_KEY
```bash
OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnop
```

| 항목 | 내용 |
|------|------|
| **용도** | Vector 임베딩 (유사도 검색) |
| **사용처** | `app/services/embedding_client.py` |
| **모델** | text-embedding-3-small |
| **발급처** | [OpenAI Platform](https://platform.openai.com/signup) |
| **비용** | $0.02/1M tokens (매우 저렴) |

**주요 메서드**:
```python
async def create_embedding(text: str) -> List[float]:
    # 스크립트 Vector 임베딩 (1536차원)
```

---

### 🔹 시스템 인증

#### 1.5 SECRET_KEY
```bash
SECRET_KEY=xK8vZpQm3nR7wL2jYhF5aD9bC1eT6uI0sG4oN8pM
```

| 항목 | 내용 |
|------|------|
| **용도** | FastAPI 세션 암호화 |
| **생성 방법** | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| **최소 길이** | 32자 이상 |

---

#### 1.6 JWT_SECRET_KEY
```bash
JWT_SECRET_KEY=bN2pM5rT8wA3xC6vD9yE1zF4hG7jK0lQ3nP6sR9uW
```

| 항목 | 내용 |
|------|------|
| **용도** | JWT 토큰 서명 |
| **생성 방법** | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| **주의** | SECRET_KEY와 **다른 값** 사용 |

---

### 🔹 YouTube OAuth2 클라이언트 설정

> **⚠️ 중요**: `YOUTUBE_API_KEY`와는 **완전히 다른 용도**입니다!

#### 1.7 YOUTUBE_CLIENT_ID & YOUTUBE_CLIENT_SECRET
```bash
YOUTUBE_CLIENT_ID=123456789012-abc123def456ghi789jkl012mno345p.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-abc123def456ghi789jkl012
OAUTH_REDIRECT_URI=http://localhost:8001/api/v1/oauth/youtube/callback
```

| 항목 | 내용 |
|------|------|
| **용도** | 사용자별 YouTube OAuth2 인증 (업로드용) |
| **사용처** | `app/utils/youtube_oauth.py` |
| **권한** | `youtube.upload`, `youtube` (Write 권한) |
| **발급처** | [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials → OAuth 2.0 Client IDs |

**발급 절차**:
1. 프로젝트 선택 (또는 생성)
2. **APIs & Services** → **Credentials**
3. **CREATE CREDENTIALS** → **OAuth client ID**
4. Application type: **Web application**
5. Authorized redirect URIs 추가:
   - `http://localhost:8001/api/v1/oauth/youtube/callback` (개발)
   - `https://yourdomain.com/api/v1/oauth/youtube/callback` (프로덕션)
6. Client ID와 Client Secret 복사

---

### 📝 전체 프로젝트용 API 키 체크리스트

```bash
# .env 파일 예시
# AI Services
YOUTUBE_API_KEY=AIzaSyD1234567890abcdefghijklmnop
GEMINI_API_KEY=AIzaSyA9876543210zyxwvutsrqponmlk
ANTHROPIC_API_KEY=sk-ant-api03-1234567890abcdef
OPENAI_API_KEY=sk-proj-1234567890abcdefghijklmnop

# System Auth
SECRET_KEY=xK8vZpQm3nR7wL2jYhF5aD9bC1eT6uI0sG4oN8pM
JWT_SECRET_KEY=bN2pM5rT8wA3xC6vD9yE1zF4hG7jK0lQ3nP6sR9uW

# YouTube OAuth2
YOUTUBE_CLIENT_ID=123456789012-abc123def456.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-abc123def456
OAUTH_REDIRECT_URI=http://localhost:8001/api/v1/oauth/youtube/callback
```

---

## 2. 사용자별 API 키

### 📍 저장 위치
`user_platform_credentials` 테이블 (PostgreSQL)

### 📊 데이터베이스 스키마

```sql
CREATE TABLE user_platform_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    credential_name VARCHAR(100),  -- "메인 채널", "서브 채널" 등
    credentials JSONB NOT NULL,    -- 🔒 암호화된 OAuth 토큰
    is_default BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'active',  -- active, expired, invalid
    last_validated TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, platform_id, credential_name)
);
```

### 🔐 플랫폼별 OAuth2 토큰 구조

#### 2.1 YouTube (업로드용)
```json
{
  "access_token": "ya29.a0AfB_byDBd1234567890abcdefghij...",
  "refresh_token": "1//0gKxS567890abcdefghijklmnopqrstuv...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": "2026-03-02T12:00:00Z",
  "scope": "https://www.googleapis.com/auth/youtube.upload"
}
```

| 필드 | 설명 |
|------|------|
| `access_token` | 실제 API 호출에 사용 (1시간 유효) |
| `refresh_token` | access_token 갱신용 (영구적) |
| `expires_at` | 만료 시간 (자동 갱신 트리거) |

**저장 방법**:
```python
# 1. 암호화 (Fernet)
encrypted_credentials = encrypt_dict_for_db({
    "access_token": "ya29.a0AfB_...",
    "refresh_token": "1//0gKxS..."
})

# 2. DB 저장
new_credential = UserPlatformCredential(
    user_id=current_user.id,
    platform_id=1,  # YouTube
    credential_name="메인 채널",
    credentials=encrypted_credentials
)
```

---

#### 2.2 TikTok
```json
{
  "client_key": "aw8j9d3k567890",
  "client_secret": "xK8vZpQm3nR7wL2j",
  "access_token": "act.example1234567890abcdefghijklmnop",
  "refresh_token": "rft.example9876543210zyxwvutsrqponmlk",
  "expires_in": 86400,
  "expires_at": "2026-03-03T12:00:00Z"
}
```

---

#### 2.3 Instagram
```json
{
  "client_id": "1234567890123456",
  "client_secret": "abc123def456ghi789jkl012",
  "access_token": "IGQVJ...1234567890",
  "user_id": "9876543210",
  "expires_in": 5184000
}
```

---

#### 2.4 기타 플랫폼
- **Facebook**: `app_id`, `app_secret`, `access_token`
- **Twitter/X**: `api_key`, `api_secret`, `access_token`, `refresh_token`
- **Snapchat**: `client_id`, `client_secret`, `access_token`
- **Pinterest**: `app_id`, `app_secret`, `access_token`
- **LinkedIn**: `client_id`, `client_secret`, `access_token`

---

### 🔄 OAuth2 Flow (YouTube 예시)

#### Step 1: 사용자가 플랫폼 인증 시작
```bash
POST /api/v1/credentials/oauth/youtube/authorize
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "redirect_uri": "http://localhost:8001/api/v1/oauth/youtube/callback"
}
```

**응답**:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&redirect_uri=...&scope=youtube.upload&state=abc123...",
  "state": "abc123def456ghi789jkl012"
}
```

#### Step 2: 사용자가 Google 동의 화면에서 승인
브라우저에서 `authorization_url`로 이동 → 계정 선택 → 권한 동의

#### Step 3: Google이 Callback URL로 리다이렉트
```
http://localhost:8001/api/v1/oauth/youtube/callback?code=4/0Adeu5BW...&state=abc123def456
```

#### Step 4: Backend가 Code → Token 교환
```bash
POST /api/v1/credentials/oauth/youtube/callback
Content-Type: application/json

{
  "code": "4/0Adeu5BW1234567890abcdefghijklmnop",
  "state": "abc123def456ghi789jkl012"
}
```

**Backend 처리**:
```python
async def youtube_callback(callback: OAuth2CallbackRequest, db: AsyncSession):
    # 1. State 검증 (Redis)
    state_data = verify_state(callback.state)
    user_id = state_data["user_id"]
    
    # 2. Authorization Code → Access Token + Refresh Token
    tokens = await exchange_code_for_tokens(callback.code, redirect_uri)
    # {
    #   "access_token": "ya29.a0AfB_...",
    #   "refresh_token": "1//0gKxS...",
    #   "expires_in": 3600
    # }
    
    # 3. 채널 정보 조회
    channel_info = await get_channel_info(tokens["access_token"])
    # {"channel_id": "UC...", "channel_title": "My Channel"}
    
    # 4. UserPlatformCredential에 암호화 저장
    encrypted = encrypt_dict_for_db(tokens)
    credential = UserPlatformCredential(
        user_id=user_id,
        platform_id=1,  # YouTube
        credential_name=channel_info["channel_title"],
        credentials=encrypted
    )
    db.add(credential)
    
    # 5. Channel 테이블에 자동 생성
    channel = Channel(
        user_credential_id=credential.id,
        channel_name=channel_info["channel_title"],
        external_channel_id=channel_info["channel_id"]
    )
    db.add(channel)
    await db.commit()
```

#### Step 5: 이후 업로드 시 자동 Token 갱신
```python
async def upload_video(user_id: int, video_data: dict, db: AsyncSession):
    # 1. 사용자의 기본 YouTube Credential 조회
    credential = await get_default_credential(user_id, platform="youtube", db)
    
    # 2. 복호화
    tokens = decrypt_dict_from_db(credential.credentials)
    
    # 3. Access Token 만료 확인
    if datetime.now(timezone.utc) >= tokens["expires_at"]:
        # 4. Refresh Token으로 갱신
        new_tokens = await refresh_access_token(tokens["refresh_token"])
        
        # 5. DB 업데이트
        credential.credentials = encrypt_dict_for_db(new_tokens)
        await db.commit()
        
        tokens = new_tokens
    
    # 6. YouTube API 호출
    youtube = build("youtube", "v3", credentials=Credentials(token=tokens["access_token"]))
    request = youtube.videos().insert(...)
```

---

## 3. 분리 관리 방식

### 🔄 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                          Admin Server                            │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  전체 프로젝트용 API 키 (.env)                          │   │
│  │                                                           │   │
│  │  🤖 AI Services                                          │   │
│  │  ├─ YOUTUBE_API_KEY ────► 트렌드 수집 (Read-Only)       │   │
│  │  ├─ GEMINI_API_KEY ─────► 트렌드 분석                   │   │
│  │  ├─ ANTHROPIC_API_KEY ──► 스크립트 생성                 │   │
│  │  └─ OPENAI_API_KEY ─────► Vector 임베딩                 │   │
│  │                                                           │   │
│  │  🔐 System Auth                                          │   │
│  │  ├─ SECRET_KEY ─────────► FastAPI Session               │   │
│  │  └─ JWT_SECRET_KEY ─────► JWT 토큰 서명                 │   │
│  │                                                           │   │
│  │  🔑 OAuth2 Client                                        │   │
│  │  ├─ YOUTUBE_CLIENT_ID                                    │   │
│  │  └─ YOUTUBE_CLIENT_SECRET                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  사용자별 API 키 (PostgreSQL - 암호화)                  │   │
│  │                                                           │   │
│  │  👤 User 1                    👤 User 2                  │   │
│  │  ├─ YouTube 메인 채널         ├─ YouTube 게임 채널      │   │
│  │  │  ├ access_token (🔒)       │  ├ access_token (🔒)    │   │
│  │  │  └ refresh_token (🔒)      │  └ refresh_token (🔒)   │   │
│  │  ├─ TikTok 계정               ├─ TikTok 계정            │   │
│  │  │  ├ access_token (🔒)       │  └ access_token (🔒)    │   │
│  │  │  └ refresh_token (🔒)      └─ Instagram 계정         │   │
│  │  └─ Instagram 계정               ├ access_token (🔒)    │   │
│  │     └ access_token (🔒)          └ user_id              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 🔐 암호화 메커니즘

#### 1. Fernet 대칭 암호화 (utils/crypto.py)
```python
from cryptography.fernet import Fernet
import os

# 암호화 키 (환경 변수에서 가져오기)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")  # Fernet 키 (32바이트 Base64)
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_dict_for_db(data: dict) -> dict:
    """
    민감한 필드만 암호화
    """
    encrypted_data = data.copy()
    sensitive_fields = [
        "access_token",
        "refresh_token",
        "api_key",
        "api_secret",
        "client_secret",
        "password"
    ]
    
    for field in sensitive_fields:
        if field in encrypted_data and encrypted_data[field]:
            # Fernet 암호화
            plaintext = str(encrypted_data[field]).encode()
            ciphertext = fernet.encrypt(plaintext)
            encrypted_data[field] = ciphertext.decode()  # Base64 문자열
    
    return encrypted_data

def decrypt_dict_from_db(data: dict) -> dict:
    """
    암호화된 필드 복호화
    """
    decrypted_data = data.copy()
    sensitive_fields = ["access_token", "refresh_token", "api_key", "api_secret", "client_secret", "password"]
    
    for field in sensitive_fields:
        if field in decrypted_data and decrypted_data[field]:
            try:
                ciphertext = decrypted_data[field].encode()
                plaintext = fernet.decrypt(ciphertext)
                decrypted_data[field] = plaintext.decode()
            except Exception as e:
                logger.error(f"Failed to decrypt {field}: {e}")
    
    return decrypted_data
```

**암호화 키 생성** (한 번만 실행):
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # .env에 ENCRYPTION_KEY로 저장
```

---

#### 2. API 응답 시 마스킹 처리
```python
def mask_sensitive_fields(credentials: dict) -> dict:
    """
    API 응답 시 민감한 정보 마스킹
    """
    masked = credentials.copy()
    sensitive_fields = ["access_token", "refresh_token", "api_key", "api_secret", "client_secret", "password"]
    
    for field in sensitive_fields:
        if field in masked and masked[field]:
            value = str(masked[field])
            if len(value) > 8:
                # 앞 4자 + **** + 뒤 4자
                masked[field] = value[:4] + "****" + value[-4:]
            else:
                masked[field] = "****"
    
    return masked

# 사용 예시
@router.get("/credentials/{credential_id}")
async def get_credential(credential_id: int, ...):
    credential = await db.get(UserPlatformCredential, credential_id)
    
    # 복호화 (내부 사용)
    decrypted = decrypt_dict_from_db(credential.credentials)
    
    # 마스킹 (API 응답)
    masked = mask_sensitive_fields(decrypted)
    
    return CredentialResponseMasked(
        id=credential.id,
        credentials=masked  # {access_token: "ya29****cdef"}
    )
```

---

### 📋 권한 체계

#### 1. 전체 프로젝트용 API 키
- **소유자**: 시스템 관리자
- **접근 권한**: Admin 서버만
- **용도**: AI 콘텐츠 생성 (모든 사용자 공유)
- **보안 레벨**: 높음 (`.env` 파일, `.gitignore` 필수)

#### 2. 사용자별 API 키
- **소유자**: 각 사용자
- **접근 권한**: 본인만 (JWT 인증)
- **용도**: 플랫폼 업로드, 채널 관리
- **보안 레벨**: 매우 높음 (DB 암호화 + API 마스킹)

---

## 4. 보안 체크리스트

### ✅ 전체 프로젝트용 API 키

- [ ] `.env` 파일을 `.gitignore`에 추가
  ```bash
  echo ".env" >> .gitignore
  ```

- [ ] `.env.example`만 Git에 커밋 (실제 값 제외)
  ```bash
  git add .env.example
  git commit -m "Add .env.example template"
  ```

- [ ] API 키를 코드에 하드코딩하지 않기
  ```python
  # ❌ 절대 하지 말 것
  YOUTUBE_API_KEY = "AIzaSyD1234567890"
  
  # ✅ 환경 변수 사용
  YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
  ```

- [ ] 프로덕션과 개발 환경 분리
  ```bash
  # 개발
  .env.development
  
  # 프로덕션
  .env.production  # 서버에만 존재, Git 제외
  ```

- [ ] API 키 정기 로테이션 (3-6개월)

- [ ] 사용량 모니터링 (무료 쿼터 초과 방지)
  - YouTube Data API: 하루 10,000 쿼터
  - Gemini: 일일 1,500 요청
  - Anthropic: 크레딧 잔액 확인
  - OpenAI: 월 사용량 확인

---

### ✅ 사용자별 API 키

- [ ] ENCRYPTION_KEY 생성 및 `.env`에 추가
  ```python
  from cryptography.fernet import Fernet
  print(Fernet.generate_key().decode())
  ```

- [ ] `credentials` JSONB 컬럼에만 민감한 정보 저장
  ```python
  # ✅ 올바른 방법
  credentials={
      "access_token": "...",  # 암호화됨
      "refresh_token": "..."  # 암호화됨
  }
  
  # ❌ 잘못된 방법
  access_token = Column(String)  # 평문 컬럼, 위험!
  ```

- [ ] API 응답 시 반드시 마스킹 처리
  ```python
  return CredentialResponseMasked(
      credentials=mask_sensitive_fields(decrypted)
  )
  ```

- [ ] JWT 인증으로 본인 자격증명만 접근 허용
  ```python
  if credential.user_id != current_user.id:
      raise HTTPException(status_code=403, detail="Forbidden")
  ```

- [ ] Access Token 자동 갱신 구현
  ```python
  if token_expired:
      new_tokens = await refresh_access_token(refresh_token)
      await update_credential(new_tokens)
  ```

- [ ] OAuth2 State 검증 (CSRF 방지)
  ```python
  state_data = verify_state(callback.state)
  if not state_data:
      raise HTTPException(status_code=400, detail="Invalid state")
  ```

- [ ] Refresh Token을 절대 API 응답에 포함하지 않기
  ```python
  # ✅ 올바른 방법 (DB에만 저장)
  db.add(UserPlatformCredential(credentials={"refresh_token": "..."}))
  
  # ❌ 잘못된 방법 (API 응답에 포함)
  return {"refresh_token": "1//0gKxS..."}  # 위험!
  ```

---

### 🔄 정기 점검 항목

#### 1. API 키 만료 확인 (매주)
```sql
-- 만료된 Credential 조회
SELECT id, user_id, platform_id, status, last_validated
FROM user_platform_credentials
WHERE status = 'expired'
OR last_validated < NOW() - INTERVAL '7 days';
```

#### 2. 사용량 모니터링 (매일)
```python
# YouTube Data API 쿼터 확인
@scheduler.task("0 22 * * *")  # 매일 22시
async def check_youtube_quota():
    # Google Cloud Console → APIs & Services → Dashboard
    # Quota 95% 이상 시 알림
```

#### 3. Refresh Token 갱신 테스트 (매월)
```python
@scheduler.task("0 3 1 * *")  # 매월 1일 03시
async def test_token_refresh():
    # 모든 플랫폼 Credential 갱신 테스트
    credentials = await get_all_credentials()
    for cred in credentials:
        try:
            await refresh_access_token(cred.refresh_token)
            cred.status = "active"
        except Exception as e:
            cred.status = "invalid"
            logger.error(f"Credential {cred.id} refresh failed: {e}")
```

---

## 📊 5. 운영 시나리오

### 시나리오 1: 새로운 사용자 등록
1. 사용자가 Admin 웹사이트에서 회원가입
2. 로그인 후 "플랫폼 연동" 페이지로 이동
3. YouTube 연동 버튼 클릭
4. Google OAuth2 동의 화면에서 승인
5. Backend가 Access Token + Refresh Token 저장 (암호화)
6. 자동으로 Channel 생성
7. 이제 Job 생성 시 해당 채널로 업로드 가능

---

### 시나리오 2: 기존 사용자가 TikTok 추가
1. "플랫폼 연동" 페이지에서 TikTok 연동 버튼 클릭
2. TikTok OAuth2 동의 화면에서 승인
3. TikTok Access Token 저장
4. 자동으로 TikTok Channel 생성
5. Job 생성 시 YouTube + TikTok 동시 업로드 가능

---

### 시나리오 3: Access Token 만료
1. Agent가 Job 실행 중 YouTube 업로드 시도
2. `401 Unauthorized` 오류 발생
3. Backend가 Refresh Token으로 자동 갱신
4. 새로운 Access Token으로 재시도
5. 업로드 성공

---

### 시나리오 4: Refresh Token 만료 (드물지만 가능)
1. YouTube API 호출 시 `invalid_grant` 오류
2. Credential status를 `expired`로 변경
3. 사용자에게 이메일 알림 발송
4. 사용자가 "플랫폼 연동" 페이지에서 재인증

---

## 🚀 6. 빠른 시작

### Step 1: 전체 프로젝트용 API 키 발급
[API_KEYS_GUIDE.md](./API_KEYS_GUIDE.md) 참고

---

### Step 2: `.env` 파일 작성
```bash
cd admin/backend
cp .env.example .env
nano .env  # 또는 메모장
```

필수 항목 입력:
```bash
# AI Services
YOUTUBE_API_KEY=AIzaSyD...  # Google Cloud Console
GEMINI_API_KEY=AIzaSyA...   # Google AI Studio
ANTHROPIC_API_KEY=sk-ant... # Anthropic Console
OPENAI_API_KEY=sk-proj...   # OpenAI Platform

# System Auth
SECRET_KEY=xK8vZpQm...      # python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=bN2pM5rT...  # python -c "import secrets; print(secrets.token_urlsafe(32))"

# YouTube OAuth2
YOUTUBE_CLIENT_ID=123456789012-abc123...apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-abc123...

# Encryption
ENCRYPTION_KEY=abc123...     # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

### Step 3: 서버 재시작
```bash
cd C:\shorts\admin\backend
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

---

### Step 4: API 테스트
```bash
# AI Integration 테스트
.\venv\Scripts\python.exe test_ai_integration.py

# OAuth Flow 테스트
.\venv\Scripts\python.exe test_oauth_flow.py
```

---

## 📞 문제 해결

### Q1: YouTube API 403 Forbidden
**원인**: YOUTUBE_API_KEY 쿼터 초과 (하루 10,000 쿼터)  
**해결**: Google Cloud Console → Quotas & System Limits 확인, 다음날 UTC 자정 리셋

### Q2: Gemini API 429 Too Many Requests
**원인**: 분당 15 요청 제한 초과  
**해결**: Rate Limiter 구현, 요청 간격 4초 이상

### Q3: OAuth2 Callback 400 Bad Request
**원인**: `redirect_uri` 불일치  
**해결**: Google Cloud Console → Authorized redirect URIs 확인

### Q4: Credential 복호화 실패
**원인**: `ENCRYPTION_KEY` 변경됨  
**해결**: 원래 키로 복구 또는 모든 Credential 재등록

---

## 📚 참고 문서

- [API_KEYS_GUIDE.md](./API_KEYS_GUIDE.md) - API 키 발급 상세 가이드
- [Google OAuth2 Guide](https://developers.google.com/identity/protocols/oauth2)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Fernet Encryption](https://cryptography.io/en/latest/fernet/)

---

**작성**: GitHub Copilot (Claude Sonnet 4.5)  
**최종 업데이트**: 2026년 3월 2일
