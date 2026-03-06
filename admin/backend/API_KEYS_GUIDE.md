# 🔑 API 키 발급 가이드

현재 시스템에서 필요한 모든 API 키 발급 방법을 단계별로 안내합니다.

---

## 📋 필수 API 키 목록

| API 키 | 용도 | 필수 여부 | 예상 비용 |
|--------|------|-----------|----------|
| **YOUTUBE_API_KEY** | YouTube 트렌드 수집 | ✅ 필수 | 무료 (쿼터 제한) |
| **GEMINI_API_KEY** | 트렌드 분석 AI | ✅ 필수 | 무료 (일일 제한) |
| **ANTHROPIC_API_KEY** | 스크립트 생성 AI | ✅ 필수 | 유료 ($5 무료 크레딧) |
| **OPENAI_API_KEY** | 임베딩 생성 (Vector) | ✅ 필수 | 유료 (매우 저렴) |
| **GOOGLE_CLOUD_PROJECT** | TTS/Translation | 🔜 Phase 2 | 유료 (사용량 기반) |
| **SECRET_KEY** | FastAPI 세션 암호화 | ✅ 필수 | 무료 (직접 생성) |
| **JWT_SECRET_KEY** | JWT 토큰 서명 | ✅ 필수 | 무료 (직접 생성) |

---

## 1️⃣ YOUTUBE_API_KEY (필수)

### 📌 용도
- YouTube 트렌드 영상 수집
- 키워드 기반 영상 검색
- 댓글 데이터 수집

### 💰 비용
- **무료**: 하루 10,000 단위 쿼터
- 트렌드 조회: 약 100 단위/요청
- 검색: 100 단위/요청
- **하루 약 100회 API 호출 가능** (충분)

### 🔧 발급 방법

#### Step 1: Google Cloud Console 접속
```
https://console.cloud.google.com
```

#### Step 2: 프로젝트 생성
1. 상단 프로젝트 선택 → **새 프로젝트**
2. 프로젝트 이름: `shorts-generator` (예시)
3. 조직: 없음 → **만들기**

#### Step 3: YouTube Data API v3 활성화
1. 좌측 메뉴 → **API 및 서비스** → **라이브러리**
2. 검색창에 `YouTube Data API v3` 입력
3. YouTube Data API v3 선택
4. **사용 설정** 클릭

#### Step 4: API 키 생성
1. 좌측 메뉴 → **API 및 서비스** → **사용자 인증 정보**
2. 상단 **+ 사용자 인증 정보 만들기** → **API 키**
3. API 키가 생성됨 → 복사

#### Step 5: API 키 제한 설정 (권장)
1. 생성된 API 키 옆 **수정** 아이콘 클릭
2. **API 제한사항** 섹션
3. **키 제한** → **API 제한**
4. **YouTube Data API v3** 선택
5. 저장

#### Step 6: .env 파일에 추가
```env
YOUTUBE_API_KEY=AIzaSyAbc123def456ghi789jkl012mno345pqr
```

### ⚠️ 주의사항
- API 키는 **절대 GitHub에 커밋하지 마세요**
- 쿼터 초과 시 403 오류 발생 (다음날 자정 UTC 리셋)
- 쿼터 모니터링: [할당량 페이지](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)

---

## 2️⃣ GEMINI_API_KEY (필수)

### 📌 용도
- YouTube 트렌드 데이터 AI 분석
- 키워드 추출
- 바이럴 가능성 평가

### 💰 비용
- **무료**: Gemini 2.0 Flash (일일 제한 있음)
  - 분당 15 요청
  - 일일 1,500 요청
- **유료**: Gemini Pro ($0.10/1M tokens)

### 🔧 발급 방법

#### Step 1: Google AI Studio 접속
```
https://makersuite.google.com/app/apikey
```

#### Step 2: Google 계정 로그인
- YouTube API와 동일한 Google 계정 사용 권장

#### Step 3: API 키 생성
1. **Get API Key** 또는 **Create API Key** 버튼 클릭
2. 프로젝트 선택:
   - 기존 Google Cloud 프로젝트 선택 (YouTube API 프로젝트)
   - 또는 **새 프로젝트 만들기**
3. API 키 생성됨 → 복사

#### Step 4: .env 파일에 추가
```env
GEMINI_API_KEY=AIzaSyDxyz789abc123def456ghi789jkl012mno
```

### ⚠️ 주의사항
- 무료 플랜은 **일일 1,500 요청 제한**
- Rate Limit: 분당 15 요청
- 프로덕션 환경에서는 유료 플랜 고려

---

## 3️⃣ ANTHROPIC_API_KEY (필수)

### 📌 용도
- AI 스크립트 생성 (Claude 3.5 Sonnet)
- Hook-Body-CTA 구조 자동 생성
- 스크립트 개선 및 최적화

### 💰 비용
- **신규 가입**: $5 무료 크레딧
- **Claude 3.5 Sonnet**:
  - Input: $3 / 1M tokens
  - Output: $15 / 1M tokens
- **예상 비용**: 스크립트 1개당 약 $0.01

### 🔧 발급 방법

#### Step 1: Anthropic Console 접속
```
https://console.anthropic.com/
```

#### Step 2: 계정 생성
1. **Sign Up** 클릭
2. 이메일 입력 → 인증 메일 확인
3. 프로필 정보 입력

#### Step 3: 결제 정보 등록
1. 좌측 메뉴 → **Settings** → **Billing**
2. **Add Payment Method**
3. 신용카드 정보 입력
4. **$5 무료 크레딧 자동 적용**

#### Step 4: API 키 생성
1. 좌측 메뉴 → **API Keys**
2. **+ Create Key** 버튼 클릭
3. 키 이름 입력: `shorts-generator` (예시)
4. API 키 생성됨 → **반드시 복사** (다시 볼 수 없음)

#### Step 5: .env 파일에 추가
```env
ANTHROPIC_API_KEY=sk-ant-api03-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
```

### ⚠️ 주의사항
- API 키는 **sk-ant-로 시작**
- 키를 잃어버리면 재발급 필요
- 무료 크레딧 소진 후 자동 과금
- 사용량 모니터링: [Usage Dashboard](https://console.anthropic.com/settings/usage)

---

## 4️⃣ OPENAI_API_KEY (필수)

### 📌 용도
- 스크립트 임베딩 생성 (text-embedding-3-small)
- Vector 유사도 검색용 1536차원 벡터

### 💰 비용
- **text-embedding-3-small**: $0.02 / 1M tokens
- **예상 비용**: 스크립트 1개당 약 $0.0001 (매우 저렴)

### 🔧 발급 방법

#### Step 1: OpenAI Platform 접속
```
https://platform.openai.com/signup
```

#### Step 2: 계정 생성
1. **Sign up** 클릭
2. 이메일 또는 Google/Microsoft 계정 연동
3. 전화번호 인증

#### Step 3: 결제 정보 등록
1. 우측 상단 프로필 → **Billing**
2. **Add payment method**
3. 신용카드 정보 입력
4. **충전 금액 설정 (최소 $5)**

#### Step 4: API 키 생성
1. 좌측 메뉴 → **API keys**
2. **+ Create new secret key** 클릭
3. 키 이름 입력: `shorts-generator` (예시)
4. 권한 선택: **All** (기본값)
5. API 키 생성됨 → **반드시 복사** (다시 볼 수 없음)

#### Step 5: .env 파일에 추가
```env
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx
```

### ⚠️ 주의사항
- API 키는 **sk-proj- 또는 sk-로 시작**
- 사용량 제한 설정 권장: [Usage limits](https://platform.openai.com/account/limits)
- 월 $5-10 예산으로 충분 (임베딩 비용 매우 저렴)

---

## 5️⃣ GOOGLE_CLOUD_PROJECT (Phase 2용)

### 📌 용도
- Google Cloud Text-to-Speech (TTS)
- Google Cloud Translation API
- 다국어 음성 합성

### 💰 비용
- **TTS**: 100만 문자당 $4-16 (음질별)
- **Translation**: 100만 문자당 $20
- **무료 할당량**:
  - TTS: 월 400만 문자
  - Translation: 월 50만 문자

### 🔧 발급 방법 (Phase 2에서 진행)

#### Step 1: Google Cloud Console
```
https://console.cloud.google.com
```

#### Step 2: 결제 계정 활성화
1. **결제** 메뉴 → **결제 계정 추가**
2. 신용카드 정보 입력
3. **무료 평가판 $300 크레딧** 활성화 (90일)

#### Step 3: Cloud TTS API 활성화
1. **API 및 서비스** → **라이브러리**
2. `Cloud Text-to-Speech API` 검색 → **사용 설정**
3. `Cloud Translation API` 검색 → **사용 설정**

#### Step 4: 서비스 계정 생성
1. **IAM 및 관리자** → **서비스 계정**
2. **+ 서비스 계정 만들기**
3. 이름: `shorts-tts-service`
4. 역할: **Cloud Translation API User**, **Cloud Text-to-Speech User**
5. **완료**

#### Step 5: JSON 키 생성
1. 생성된 서비스 계정 클릭
2. **키** 탭 → **키 추가** → **새 키 만들기**
3. **JSON** 선택 → **만들기**
4. JSON 파일 다운로드

#### Step 6: .env 파일에 추가
```env
GOOGLE_CLOUD_PROJECT_ID=shorts-generator-123456
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-key.json
```

JSON 키 파일 저장:
```
C:\shorts\admin\backend\credentials\google-cloud-key.json
```

---

## 6️⃣ SECRET_KEY & JWT_SECRET_KEY (필수)

### 📌 용도
- **SECRET_KEY**: FastAPI 세션 암호화
- **JWT_SECRET_KEY**: JWT 토큰 서명

### 💰 비용
- 무료 (직접 생성)

### 🔧 생성 방법

#### 방법 1: Python으로 생성 (권장)
```powershell
cd C:\shorts\admin\backend
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
```

출력 예시:
```
xK8vZpQm3nR7wL2jYhF5aD9bC1eT6uI0sG4oN8pM
```

#### 방법 2: PowerShell로 생성
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

#### Step 3: .env 파일에 추가
```env
SECRET_KEY=xK8vZpQm3nR7wL2jYhF5aD9bC1eT6uI0sG4oN8pM_생성된키1
JWT_SECRET_KEY=zN9mL4hF3qP7wK2jXcV6bT1rE8yU5iO0sD9gA4nM_생성된키2
```

### ⚠️ 주의사항
- **최소 32자 이상** 사용
- **두 키는 서로 다른 값** 사용
- **절대 GitHub에 커밋하지 마세요**
- 프로덕션 환경에서는 환경변수로 주입

---

## 📝 최종 .env 파일 예시

```env
# Application
APP_NAME=AI Shorts Generator Admin
APP_ENV=development
DEBUG=True
SECRET_KEY=xK8vZpQm3nR7wL2jYhF5aD9bC1eT6uI0sG4oN8pM

# Server
HOST=0.0.0.0
PORT=8001

# Database
DATABASE_URL=postgresql+asyncpg://shorts_admin:shorts_password_2026@localhost:5433/shorts_db
DATABASE_ECHO=True

# Redis
REDIS_URL=redis://:redis_password_2026@localhost:6379/0
REDIS_PASSWORD=redis_password_2026

# JWT
JWT_SECRET_KEY=zN9mL4hF3qP7wK2jXcV6bT1rE8yU5iO0sD9gA4nM
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Google Cloud (AI Services) - Phase 2
GOOGLE_APPLICATION_CREDENTIALS=./credentials/google-cloud-key.json
GOOGLE_CLOUD_PROJECT_ID=shorts-generator-123456

# ✅ YouTube Data API (필수)
YOUTUBE_API_KEY=AIzaSyAbc123def456ghi789jkl012mno345pqr

# ✅ Gemini API (필수)
GEMINI_API_KEY=AIzaSyDxyz789abc123def456ghi789jkl012mno

# ✅ Claude API (필수)
ANTHROPIC_API_KEY=sk-ant-api03-abc123def456ghi789jkl012mno345pqr678stu901vwx234yz

# ✅ OpenAI API (필수)
OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012mno345pqr678stu901vwx

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# File Storage
UPLOAD_DIR=./storage/uploads
VIDEO_DIR=./storage/videos
TEMP_DIR=./storage/temp

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=./logs/app.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
```

---

## 💰 총 비용 예상 (개발 환경)

### 초기 비용
| 항목 | 비용 |
|------|------|
| YouTube API | 무료 (쿼터 제한) |
| Gemini API | 무료 (일일 제한) |
| Anthropic (Claude) | $5 무료 크레딧 |
| OpenAI (Embeddings) | $5 최소 충전 |
| **합계** | **$10** |

### 월 운영 비용 (하루 100회 테스트)
| 항목 | 비용 |
|------|------|
| YouTube API | 무료 |
| Gemini API | 무료 |
| Claude (스크립트 생성) | ~$3/월 |
| OpenAI (임베딩) | ~$0.30/월 |
| **합계** | **~$3.30/월** |

### 프로덕션 비용 (하루 1,000회)
| 항목 | 비용 |
|------|------|
| YouTube API | 무료 또는 종량제 |
| Gemini API | ~$10/월 (유료 플랜) |
| Claude | ~$30/월 |
| OpenAI | ~$3/월 |
| Google Cloud TTS | ~$10/월 |
| **합계** | **~$53/월** |

---

## ✅ API 키 설정 체크리스트

### Phase 1 (현재) - 필수
- [ ] YouTube API 키 발급 및 .env 설정
- [ ] Gemini API 키 발급 및 .env 설정
- [ ] Anthropic API 키 발급 및 .env 설정 ($5 충전)
- [ ] OpenAI API 키 발급 및 .env 설정 ($5 충전)
- [ ] SECRET_KEY 생성 및 .env 설정
- [ ] JWT_SECRET_KEY 생성 및 .env 설정
- [ ] .env 파일 GitHub에 추가하지 않았는지 확인

### Phase 2 (다음) - 선택
- [ ] Google Cloud 프로젝트 생성
- [ ] Cloud TTS API 활성화
- [ ] Cloud Translation API 활성화
- [ ] 서비스 계정 JSON 키 생성
- [ ] credentials/google-cloud-key.json 저장

---

## 🚀 빠른 시작 가이드

### 1단계: API 키 모두 발급 (약 30분 소요)
```
1. YouTube API 키 (5분)
2. Gemini API 키 (2분)
3. Anthropic API 키 (10분 - 결제 정보 입력)
4. OpenAI API 키 (10분 - 결제 정보 입력)
5. SECRET_KEY 생성 (1분)
```

### 2단계: .env 파일 수정
```powershell
cd C:\shorts\admin\backend
notepad .env
```

모든 API 키를 복사해서 붙여넣기

### 3단계: 서버 재시작
```powershell
cd C:\shorts\admin\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4단계: API 테스트
```powershell
.\venv\Scripts\python.exe test_ai_integration.py
```

---

## 🔐 보안 주의사항

### 절대 하지 말아야 할 것
- ❌ API 키를 GitHub에 커밋
- ❌ API 키를 코드에 하드코딩
- ❌ API 키를 슬랙/이메일로 전송
- ❌ 공개 채널에 API 키 노출

### 권장 사항
- ✅ .env 파일은 .gitignore에 추가
- ✅ 환경변수로 API 키 관리
- ✅ 정기적으로 API 키 로테이션
- ✅ 사용량 모니터링 설정
- ✅ API 키별 사용 제한 설정

---

## 📞 문제 해결

### YouTube API 403 오류
→ 쿼터 초과. 다음날 자정(UTC) 까지 대기 또는 쿼터 증가 요청

### Gemini API Rate Limit
→ 분당 15 요청 제한. API 호출 간 4초 딜레이 추가

### Anthropic 크레딧 부족
→ [Billing 페이지](https://console.anthropic.com/settings/billing)에서 충전

### OpenAI 429 오류
→ Rate Limit 초과. [Limits 페이지](https://platform.openai.com/account/limits)에서 확인

---

**작성일**: 2026-03-02  
**버전**: 1.0  
**대상**: Sprint 9-10 완료 후 API 키 설정
