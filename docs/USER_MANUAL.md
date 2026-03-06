# 쇼츠 영상 자동화 플랫폼 사용 메뉴얼

**버전**: 1.0  
**최종 수정일**: 2026년 3월 3일  
**대상**: 관리자 및 콘텐츠 크리에이터

---

## 📚 목차

1. [시스템 소개](#1-시스템-소개)
2. [시작하기](#2-시작하기)
3. [Admin Dashboard 사용법](#3-admin-dashboard-사용법)
4. [Android Agent 사용법](#4-android-agent-사용법)
5. [YouTube 게시 가이드](#5-youtube-게시-가이드)
6. [TikTok 게시 가이드](#6-tiktok-게시-가이드)
7. [할당량 관리](#7-할당량-관리)
8. [트러블슈팅](#8-트러블슈팅)
9. [FAQ](#9-faq)

---

## 1. 시스템 소개

### 1.1 개요
쇼츠 영상 자동화 플랫폼은 YouTube Shorts 및 TikTok 영상을 자동으로 생성, 관리, 게시할 수 있는 통합 솔루션입니다.

### 1.2 주요 기능
- ✅ **자동 영상 생성**: Android 기기에서 스크립트 기반 영상 자동 생성
- ✅ **멀티 플랫폼 게시**: YouTube, TikTok 동시 게시 지원
- ✅ **트렌드 분석**: 실시간 트렌드 키워드 수집 및 활용
- ✅ **AI 스크립트 생성**: Claude AI 기반 자동 스크립트 작성
- ✅ **할당량 관리**: 플랫폼별 업로드 제한 관리
- ✅ **실시간 모니터링**: Agent 및 Job 상태 실시간 확인

### 1.3 시스템 구성
- **Admin Dashboard**: 웹 기반 관리 인터페이스 (http://localhost:3000)
- **Backend API**: FastAPI 기반 REST API 서버
- **Android Agent**: 영상 생성 앱 (Android 기기)
- **PostgreSQL**: 데이터베이스
- **Redis**: 캐시 및 메시지 큐
- **Celery**: 백그라운드 작업 처리

---

## 2. 시작하기

### 2.1 시스템 시작

#### Windows 환경
1. 프로젝트 폴더로 이동: `cd c:\shorts`
2. 시작 스크립트 실행:
   ```bash
   .\START-UAT.bat
   ```
3. 모든 서비스가 자동으로 시작됩니다:
   - PostgreSQL (Docker)
   - Redis (Docker)
   - Backend 서버 (포트 8001)
   - Celery Worker
   - Celery Beat
   - Frontend (포트 3000)

#### 수동 시작 (개별 서비스)
```bash
# 1. Docker 서비스
.\start-docker.bat

# 2. Backend
cd admin\backend
.\.venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 3. Celery Worker (새 터미널)
cd admin\backend
.\.venv\Scripts\activate
.\start-celery-worker.bat

# 4. Celery Beat (새 터미널)
cd admin\backend
.\.venv\Scripts\activate
.\start-celery-beat.bat

# 5. Frontend (새 터미널)
cd admin\frontend
npm run dev
```

### 2.2 첫 접속

1. 브라우저에서 http://localhost:3000 접속
2. 첫 화면에서 "회원가입" 버튼 클릭
3. 정보 입력:
   - **사용자명**: 영문자/숫자 조합 (예: `admin1`)
   - **이메일**: 유효한 이메일 형식 (예: `admin@example.com`)
   - **비밀번호**: 최소 8자, 영문/숫자/특수문자 조합
4. "회원가입" 버튼 클릭
5. 자동으로 로그인 화면으로 이동
6. 로그인 정보 입력 후 Dashboard 진입

### 2.3 시스템 상태 확인

Dashboard 상단의 **Health Status** 섹션 확인:
- ✅ **API**: Backend 서버 상태
- ✅ **Database**: PostgreSQL 연결 상태
- ✅ **Redis**: Redis 서버 상태

모두 "healthy" 상태여야 정상입니다.

---

## 3. Admin Dashboard 사용법

### 3.1 Dashboard 레이아웃

```
┌─────────────────────────────────────────────┐
│ [로고] 쇼츠 자동화     사용자명 [로그아웃]  │
├─────────────────────────────────────────────┤
│                                             │
│  Health Status: API ✓ DB ✓ Redis ✓         │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │   Agents     │  │    Jobs      │        │
│  │   목록/통계   │  │   목록/통계   │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │  Platforms   │  │ Credentials  │        │
│  │   플랫폼      │  │   인증 정보   │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │   Trends     │  │   Scripts    │        │
│  │   트렌드      │  │  스크립트     │        │
│  └──────────────┘  └──────────────┘        │
│                                             │
│  ┌────────────────────────────────┐        │
│  │      Upload Quotas             │        │
│  │      할당량 관리                │        │
│  └────────────────────────────────┘        │
│                                             │
└─────────────────────────────────────────────┘
```

### 3.2 Agent 관리

#### Agent 목록 확인
**위치**: Dashboard > Agents 섹션

**표시 정보**:
- **Device Name**: Agent 이름
- **Status**: 상태 (online/offline)
- **Last Heartbeat**: 마지막 연결 시간
- **Disk Usage**: 디스크 사용률 (있는 경우)

**상태 표시**:
- 🟢 **Online**: Agent가 정상 작동 중 (30초 이내 heartbeat)
- ⚪ **Offline**: Agent 연결 끊김 (30초 이상 heartbeat 없음)

#### Agent 통계
- **Total**: 전체 등록된 Agent 수
- **Online**: 현재 활성 Agent 수
- **Offline**: 비활성 Agent 수

#### Agent 디스크 정리
1. Agent 항목의 **"디스크 정리"** 버튼 클릭
2. 확인 창에서 "확인" 클릭
3. Agent의 임시 파일이 정리됩니다

### 3.3 Job 관리

#### Job 생성
**위치**: Dashboard > Jobs 섹션 > "Job 생성" 폼

**입력 필드**:
1. **플랫폼**: 드롭다운에서 선택 (YouTube, TikTok 등)
2. **제목**: 영상 제목 (최대 100자)
3. **스크립트**: 영상에 사용될 텍스트 (여러 줄 가능)
4. **우선순위**: 1-10 (높을수록 우선 처리)

**생성 절차**:
1. 모든 필드 입력
2. "Job 생성" 버튼 클릭
3. 성공 메시지 확인
4. Jobs 목록에 새 Job 표시

#### Job 상태
- 🟡 **Pending**: 대기 중 (Agent 할당 대기)
- 🔵 **Assigned**: Agent에 할당됨
- 🟣 **Rendering**: 영상 렌더링 중
- 🟠 **Uploading**: 파일 업로드 중
- 🟢 **Completed**: 완료
- 🔴 **Failed**: 실패
- ⚫ **Cancelled**: 취소됨

#### Job 작업
각 Job 항목 우측의 버튼:
- **"취소"**: `pending` 또는 `assigned` 상태일 때 Job 취소
- **"재시도"**: `failed` 상태일 때 다시 시도
- **"YouTube 게시"**: `completed` 상태일 때 YouTube에 업로드
- **"TikTok 게시"**: `completed` 상태일 때 TikTok에 업로드

#### Job 상세 정보
Job 제목을 클릭하면 상세 정보 표시:
- Job ID
- 생성 시각
- 완료 시각
- video_path (생성된 파일 경로)
- video_url (다운로드 URL)
- job_metadata (추가 정보, YouTube/TikTok 업로드 결과 등)

### 3.4 Platform 관리

**위치**: Dashboard > Platforms 섹션

**지원 플랫폼**:
- **YouTube**: YouTube Shorts
- **TikTok**: TikTok 영상
- **Instagram**: Instagram Reels (향후 지원)

각 플랫폼 정보:
- Platform Name
- Required Fields (필수 입력 필드)
- Max Duration (최대 영상 길이)

### 3.5 Credential 관리

#### YouTube OAuth Credential 생성

**전제 조건**: Google Cloud Console에서 OAuth Client ID 생성 완료

**단계**:
1. **Credentials** 섹션으로 이동
2. **"YouTube OAuth 시작"** 버튼 클릭
3. 새 탭에서 Google 로그인 화면 표시
4. Google 계정 로그인
5. 권한 허용 화면에서 "허용" 클릭
6. Redirect된 URL에서 다음 파라미터 확인:
   - `state`: OAuth 상태 코드
   - `code`: Authorization 코드
7. Dashboard로 돌아와서:
   - "OAuth state" 입력란에 `state` 값 붙여넣기
   - "OAuth code" 입력란에 `code` 값 붙여넣기
8. **"OAuth 콜백 처리"** 버튼 클릭
9. 성공 메시지 확인
10. Credentials 목록에 YouTube credential 표시

#### TikTok Cookie Credential 생성

**전제 조건**: TikTok 계정

**단계**:
1. Chrome/Edge 브라우저에서 https://www.tiktok.com 접속
2. TikTok 계정으로 로그인
3. 개발자 도구 열기 (F12 키)
4. "Application" 탭 → "Cookies" → "https://www.tiktok.com"
5. 다음 쿠키들 복사:
   - `sessionid`
   - `tt_csrf_token`
   - `s_v_web_id`
   - `ttwid`
6. 다음 JSON 형식으로 변환:
```json
[
  {
    "name": "sessionid",
    "value": "복사한_sessionid_값",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "tt_csrf_token",
    "value": "복사한_tt_csrf_token_값",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "s_v_web_id",
    "value": "복사한_s_v_web_id_값",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "ttwid",
    "value": "복사한_ttwid_값",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  }
]
```
7. Dashboard의 **Credentials** 섹션으로 이동
8. "Credential 생성" 폼 작성:
   - **플랫폼**: TikTok 선택
   - **Credential 이름**: `TikTok Main` (또는 원하는 이름)
   - **Credential JSON**: 위의 JSON 전체 붙여넣기
9. "Credential 생성" 버튼 클릭
10. 성공 메시지 확인

### 3.6 Trend 관리

#### 트렌드 수집
**위치**: Dashboard > Trends 섹션

**단계**:
1. "Region" 입력란에 지역 코드 입력 (예: `KR`, `US`, `JP`)
2. **"트렌드 수집"** 버튼 클릭
3. 백그라운드에서 Celery Worker가 트렌드 수집 시작
4. 약 30초-1분 후 페이지 새로고침
5. Trends 목록에 새 키워드 표시

#### 트렌드 확인
각 트렌드 항목:
- **Keyword**: 트렌드 키워드
- **Platform**: 출처 (YouTube/TikTok)
- **Region**: 지역
- **Collected At**: 수집 시각

#### 트렌드 활용
1. 트렌드 키워드를 복사
2. **Scripts** 섹션으로 이동
3. "주제" 입력란에 키워드 붙여넣기
4. 스크립트 생성 (AI 설정 시)

### 3.7 Script 관리

#### 스크립트 조회
**위치**: Dashboard > Scripts 섹션

목록에 표시되는 정보:
- 제목
- 품질 점수 (Quality Score)
- 바이럴 가능성 (Viral Potential)
- 생성 시각

#### AI 스크립트 생성 (선택적)
**전제 조건**: Claude AI 또는 OpenAI API 키 설정

**단계**:
1. "스크립트 생성" 폼 작성:
   - **주제**: 원하는 주제 (예: "여름 휴가 팁")
   - **트렌드 ID**: (선택) 트렌드 기반 생성 시 선택
   - **타겟 청중**: (선택) 예: "10-30대"
   - **플랫폼**: YouTube 또는 TikTok
   - **언어**: 한국어, 영어 등
   - **길이**: 초 단위 (예: 60)
2. "스크립트 생성" 버튼 클릭
3. AI가 Hook-Body-CTA 구조로 스크립트 생성
4. 생성된 스크립트를 Job 생성에 활용

### 3.8 Upload Quota 관리

#### 할당량 생성
**위치**: Dashboard > Upload Quotas 섹션

**단계**:
1. "할당량 생성" 폼 작성:
   - **플랫폼**: YouTube, TikTok 등 선택
   - **일일**: 하루 최대 업로드 수 (예: 3)
   - **주간**: 주 최대 업로드 수 (예: 15)
   - **월간**: 월 최대 업로드 수 (예: 50)
2. "할당량 생성" 버튼 클릭
3. 목록에 새 할당량 표시

**주의**: 사용자당 플랫폼별로 1개만 생성 가능

#### 할당량 확인
각 할당량 항목:
- **Platform ID**: 플랫폼 번호
- **D/W/M**: 일일/주간/월간 제한
- **사용**: 현재 사용량 (used_today/used_week/used_month)

#### 할당량 수정 (상향)
1. 할당량 항목의 **"상향"** 버튼 클릭
2. 자동으로 다음 값으로 증가:
   - 일일: +1
   - 주간: +5
   - 월간: +20
3. 변경 사항 즉시 반영

#### 할당량 삭제
1. 할당량 항목의 **"삭제"** 버튼 클릭
2. 확인 창: "정말로 이 할당량을 삭제하시겠습니까?" → **확인**
3. 목록에서 제거됨

**주의**: 삭제 후 복구 불가

#### 할당량 리셋
**위치**: Upload Quotas 섹션 상단 버튼

**리셋 옵션**:
- **"Daily 초기화"**: 모든 사용자의 `used_today`를 0으로
- **"Weekly 초기화"**: 모든 사용자의 `used_week`을 0으로
- **"Monthly 초기화"**: 모든 사용자의 `used_month`을 0으로

**자동 리셋**:
- 매일 00:00 - Daily 자동 리셋
- 매주 월요일 00:00 - Weekly 자동 리셋
- 매월 1일 00:00 - Monthly 자동 리셋
(Celery Beat가 실행 중일 때)

---

## 4. Android Agent 사용법

### 4.1 앱 설치

#### APK 파일 다운로드
개발팀으로부터 APK 파일을 받거나, 다음 경로에서 빌드:
```bash
cd admin/agent
npm run build:android
```
출력: `admin/agent/android/app/build/outputs/apk/release/app-release.apk`

#### 설치 방법
**옵션 1**: USB 연결
```bash
adb install app-release.apk
```

**옵션 2**: 파일 전송
1. APK 파일을 Android 기기로 전송
2. 파일 관리자에서 APK 파일 선택
3. "설치" 버튼 클릭
4. 알 수 없는 소스 허용 (설정에서)

### 4.2 첫 실행 및 설정

#### 앱 실행
1. 앱 목록에서 "Shorts Agent" 아이콘 클릭
2. 첫 화면 표시

#### Settings 탭 설정
1. 하단의 **"Settings"** 탭 클릭
2. 설정 입력:

**Backend URL**:
- PC의 IP 주소 확인:
  - Windows: `ipconfig` 명령어 실행
  - IPv4 주소 확인 (예: 192.168.1.100)
- URL 형식: `http://[PC_IP]:8001`
- 예시: `http://192.168.1.100:8001`

**Device Name**:
- 원하는 이름 입력 (예: "My Phone", "Test Device 1")
- 한글 가능

3. **"Register"** 버튼 클릭
4. 성공 메시지 확인:
   - "Registration successful"
   - Agent ID 자동 생성 및 표시

### 4.3 Home 탭 사용

#### 화면 구성
```
┌──────────────────────────────┐
│   Shorts Agent               │
├──────────────────────────────┤
│                              │
│  Agent Status: Online ✓      │
│                              │
│  ┌─────────────────────────┐ │
│  │  Pending Jobs: 0        │ │
│  │  Assigned Jobs: 0       │ │
│  │  Completed Jobs: 5      │ │
│  └─────────────────────────┘ │
│                              │
│  ┌─────────────────────────┐ │
│  │  Current Job            │ │
│  │  (없음)                  │ │
│  └─────────────────────────┘ │
│                              │
│  ┌─────────────────────────┐ │
│  │  Recent Jobs            │ │
│  │  • Job #123 - Completed │ │
│  │  • Job #122 - Completed │ │
│  └─────────────────────────┘ │
│                              │
├──────────────────────────────┤
│ [Home]   [Settings]          │
└──────────────────────────────┘
```

#### 자동 처리 흐름
1. **Polling**: 30초마다 자동으로 Backend에 새 Job 확인
2. **Job 수신**: `pending` 상태의 Job이 있으면 자동 할당
3. **Rendering**: FFmpeg으로 영상 렌더링 시도
   - 성공: 실제 mp4 파일 생성
   - 실패: Placeholder 영상 생성 (fallback)
4. **Uploading**: Backend에 파일 업로드
5. **Completion**: Job 상태를 `completed`로 업데이트
6. **반복**: 다음 Job 확인

#### 상태 확인
- **Agent Status**:
  - 🟢 Online: 정상 동작 (heartbeat 전송 중)
  - 🔴 Offline: 연결 끊김
- **Job Counts**:
  - Pending: 대기 중인 Job 수
  - Assigned: 현재 처리 중인 Job 수
  - Completed: 완료한 Job 수

#### 수동 새로고침
화면을 아래로 당겨서 수동으로 데이터 새로고침 가능

### 4.4 주의사항

#### 배터리 관리
- 앱이 백그라운드에서 계속 실행됨
- 배터리 최적화 해제 권장:
  1. 설정 → 앱 → Shorts Agent
  2. 배터리 → 배터리 최적화 → 최적화 안 함

#### 네트워크 연결
- Wi-Fi 연결 권장 (영상 업로드 용량)
- 모바일 데이터 사용 시 데이터 요금 주의

#### 저장 공간
- 생성된 영상은 업로드 후 자동 삭제
- 최소 500MB 여유 공간 권장

---

## 5. YouTube 게시 가이드

### 5.1 준비 사항

#### Google Cloud Console 설정
1. https://console.cloud.google.com 접속
2. 프로젝트 생성 또는 기존 프로젝트 선택
3. "APIs & Services" → "Library"
4. "YouTube Data API v3" 검색 및 활성화
5. "APIs & Services" → "Credentials"
6. "Create Credentials" → "OAuth 2.0 Client ID"
7. Application type: "Web application"
8. Authorized redirect URIs 추가:
   - `http://localhost:8001/api/v1/credentials/youtube/oauth-callback`
9. Client ID 및 Client Secret 저장

#### 환경 변수 설정
`admin/backend/.env` 파일에 추가:
```env
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
```

Backend 서버 재시작

### 5.2 YouTube Credential 생성
[3.5 Credential 관리](#35-credential-관리) 참고

### 5.3 영상 게시

#### 게시 단계
1. Dashboard의 **Jobs** 섹션으로 이동
2. `completed` 상태인 Job 찾기
3. Job 우측의 **"YouTube 게시"** 버튼 클릭
4. 확인 창: "이 영상을 YouTube에 게시하시겠습니까?" → **확인**
5. 처리 대기 (10-30초)
6. 성공 메시지 확인: "YouTube 게시 완료"

#### 게시 옵션 (고급)
현재 버전에서는 기본 설정 사용:
- **제목**: Job의 title 사용
- **설명**: 자동 생성 (스크립트 내용)
- **공개 상태**: Private (비공개)
- **태그**: 자동 생성

향후 버전에서 커스터마이징 추가 예정

### 5.4 YouTube Studio 확인

1. https://studio.youtube.com 접속
2. 왼쪽 메뉴에서 **"콘텐츠"** 클릭
3. 최근 업로드된 영상 확인
4. 영상 클릭하여 상세 정보 확인:
   - 제목/설명 수정 가능
   - 공개 상태 변경 가능 (Private → Public)
   - 썸네일 추가 가능

### 5.5 할당량 주의사항

#### YouTube API 할당량
- **일일 할당량**: 10,000 units (Google 기본 제공)
- **영상 업로드 비용**: 1,600 units/영상
- **일일 최대**: 약 6개 영상 업로드 가능

할당량 초과 시:
- 게시 실패: "Quota exceeded" 에러
- 다음날 00:00 (PST) 자동 리셋

#### 플랫폼 Upload Quota
Dashboard에서 설정한 Upload Quota도 적용됨
- YouTube API 할당량과 별개
- 관리자가 직접 제어 가능

---

## 6. TikTok 게시 가이드

### 6.1 준비 사항

#### Playwright 브라우저 설치
```bash
cd admin/backend
.\.venv\Scripts\activate
playwright install chromium
```

#### TikTok 계정
- 테스트용 TikTok 계정 준비
- 2단계 인증 해제 권장 (자동화 용이)

### 6.2 TikTok Credential 생성
[3.5 Credential 관리](#35-credential-관리) 참고

### 6.3 영상 게시

#### 게시 단계
1. Dashboard의 **Jobs** 섹션
2. `completed` 상태인 Job 선택
3. **"TikTok 게시"** 버튼 클릭
4. 확인 창: "이 영상을 TikTok에 게시하시겠습니까?" → **확인**
5. 처리 대기 (30초-1분)
   - Backend에서 Playwright 브라우저 자동 실행
   - TikTok 로그인 및 업로드 자동화
6. 성공 메시지 확인

#### 게시 프로세스
1. Playwright가 Chromium 브라우저 실행 (headless 모드)
2. TikTok 쿠키로 자동 로그인
3. Upload 페이지로 이동
4. 영상 파일 선택 및 업로드
5. 캡션 입력 (Job의 title 또는 script)
6. "게시" 버튼 클릭
7. 완료 확인 후 브라우저 종료

### 6.4 TikTok에서 확인

1. https://www.tiktok.com/@your_username 접속
2. 프로필 페이지에서 최신 영상 확인
3. 영상 클릭하여 재생 테스트
4. 캡션/해시태그 확인

### 6.5 문제 해결

#### 쿠키 만료
**증상**: "Invalid session" 에러

**해결**:
1. 브라우저에서 TikTok 다시 로그인
2. 쿠키 다시 추출
3. Credential 업데이트

**쿠키 유효 기간**: 일반적으로 30일, 로그인 활동에 따라 연장

#### 업로드 실패
**증상**: "Upload failed" 에러

**가능한 원인**:
- TikTok 정책 위반 (저작권, 부적절한 콘텐츠)
- 영상 형식/크기 문제
- 네트워크 연결 불안정

**해결**:
- Backend 로그 확인: `admin/backend/logs/app.log`
- Playwright 브라우저 스크린샷 확인 (디버그 모드)

---

## 7. 할당량 관리

### 7.1 할당량 개념

#### 왜 할당량이 필요한가?
- **플랫폼 정책 준수**: YouTube/TikTok의 스팸 방지
- **API 할당량 관리**: YouTube API 일일 제한 준수
- **비용 관리**: API 호출 비용 제어
- **품질 관리**: 과도한 업로드 방지

#### 할당량 종류
- **일일 (Daily)**: 하루 최대 업로드 수
- **주간 (Weekly)**: 일주일 최대 업로드 수
- **월간 (Monthly)**: 한 달 최대 업로드 수

### 7.2 할당량 설정 전략

#### 추천 설정 (YouTube)
- **개인 사용자**:
  - Daily: 2-3
  - Weekly: 10-15
  - Monthly: 30-50
- **비즈니스 사용자**:
  - Daily: 5-7
  - Weekly: 30-40
  - Monthly: 100-150

#### 추천 설정 (TikTok)
- **개인 사용자**:
  - Daily: 3-5
  - Weekly: 15-20
  - Monthly: 50-80
- **비즈니스 사용자**:
  - Daily: 8-10
  - Weekly: 40-50
  - Monthly: 150-200

### 7.3 할당량 모니터링

#### 실시간 확인
Dashboard의 **Upload Quotas** 섹션에서 실시간 확인:
```
platform_id=1 · D/W/M 3/15/50
사용 2/8/25
```
- **D/W/M**: 제한 (일일/주간/월간)
- **사용**: 현재 사용량

#### 할당량 상태
- ✅ **여유**: 사용량 < 제한의 80%
- ⚠️ **주의**: 사용량 80-95%
- 🚫 **초과**: 사용량 ≥ 100%

### 7.4 할당량 초과 대응

#### 업로드 차단
할당량 초과 시 자동 차단:
- YouTube/TikTok 게시 버튼 클릭 시 에러 발생
- 에러 메시지: "Daily/Weekly/Monthly limit exceeded"

#### 대응 방법
**옵션 1**: 자동 리셋 대기
- Daily: 다음날 00:00까지 대기
- Weekly: 다음 월요일 00:00까지 대기
- Monthly: 다음 달 1일 00:00까지 대기

**옵션 2**: 수동 리셋
1. Dashboard > Upload Quotas
2. "Daily 초기화" 버튼 클릭 (관리자 권한 필요)
3. 즉시 사용량이 0으로 초기화

**옵션 3**: 할당량 상향
1. 할당량 항목의 "상향" 버튼 클릭
2. 제한이 자동으로 증가

---

## 8. 트러블슈팅

### 8.1 시스템 시작 실패

#### Frontend 빌드 실패
**증상**: 
```
npm run build
Error: ENOENT: no such file or directory
```

**해결**:
```bash
cd admin/frontend
npm install
npm run build
```

#### Backend 서버 시작 실패
**증상**:
```
Address already in use
```

**해결**:
```bash
# 포트 8001 사용 중인 프로세스 확인 및 종료
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

#### Docker 서비스 실패
**증상**: "Cannot connect to Docker daemon"

**해결**:
1. Docker Desktop 실행 확인
2. Docker 서비스 재시작
   ```bash
   net stop com.docker.service
   net start com.docker.service
   ```

### 8.2 로그인/인증 문제

#### 로그인 실패
**증상**: "아이디 또는 비밀번호가 올바르지 않습니다"

**확인 사항**:
- 사용자명 정확히 입력 (대소문자 구분)
- 비밀번호 정확히 입력
- 회원가입 완료 여부 확인

**해결**:
- 회원가입 다시 시도 (다른 사용자명)
- 브라우저 캐시 삭제
- 시크릿 모드에서 시도

#### 세션 만료
**증상**: "세션이 만료되었습니다. 다시 로그인해주세요."

**해결**:
1. 로그아웃 버튼 클릭
2. 다시 로그인

### 8.3 Agent 연결 문제

#### Agent 등록 실패
**증상**: "Registration failed"

**확인 사항**:
1. Backend URL 정확한지 확인
2. PC와 Android 기기가 같은 네트워크에 있는지
3. Backend 서버가 실행 중인지

**해결**:
```bash
# PC IP 확인
ipconfig

# Backend URL 형식 확인
http://[PC_IP]:8001
# 예: http://192.168.1.100:8001
```

#### Agent Offline 상태
**증상**: Dashboard에서 Agent가 계속 offline

**해결**:
1. Android 앱 재시작
2. Settings에서 "Register" 다시 클릭
3. 네트워크 연결 확인
4. Backend 로그 확인

### 8.4 Job 처리 문제

#### Job이 계속 Pending
**증상**: Job이 `pending` 상태에서 변하지 않음

**확인 사항**:
- Agent가 online 상태인지
- Agent가 다른 Job 처리 중인지

**해결**:
1. Agent 확인 및 재시작
2. 30초 대기 (자동 폴링 주기)
3. Job 우선순위 확인 (낮으면 나중에 처리)

#### 영상 생성 실패
**증상**: Job이 `failed` 상태

**확인 사항**:
- Agent 로그 확인
- FFmpeg 설치 여부 (없으면 placeholder 생성됨)

**해결**:
1. Job "재시도" 버튼 클릭
2. Agent 재시작
3. 스크립트 내용 확인 (특수문자 포함 여부)

### 8.5 게시 실패

#### YouTube 게시 실패 (401)
**증상**: "Failed to publish: 401 Unauthorized"

**해결**:
1. YouTube OAuth 재인증
2. Credential 삭제 후 다시 생성
3. Google Cloud Console에서 OAuth Client 확인

#### YouTube 게시 실패 (403)
**증상**: "Failed to publish: 403 Quota exceeded"

**원인**: YouTube API 할당량 초과

**해결**:
- 다음날까지 대기
- 또는 Google Cloud Console에서 할당량 증액 신청

#### TikTok 게시 실패
**증상**: "TikTok upload failed"

**해결**:
1. TikTok 쿠키 재추출
2. Credential 업데이트
3. Playwright 브라우저 재설치
   ```bash
   cd admin/backend
   playwright install chromium
   ```

### 8.6 성능 문제

#### Dashboard 느림
**원인**: 대량의 Job/Agent 데이터

**해결**:
1. 브라우저 캐시 삭제
2. 완료된 Job 자동 삭제 (설정에서)
3. Database 인덱스 최적화 (관리자 문의)

#### Agent 영상 처리 느림
**원인**: 기기 성능 부족

**해결**:
- 다른 앱 종료하여 메모리 확보
- 기기 재시작
- 더 높은 사양의 기기 사용

---

## 9. FAQ

### 9.1 일반

**Q: 이 시스템은 무료인가요?**
A: 시스템 자체는 오픈소스(또는 라이센스에 따름)이지만, YouTube/TikTok API 사용 시 각 플랫폼의 정책에 따라 제한이 있을 수 있습니다.

**Q: 여러 계정으로 동시에 사용할 수 있나요?**
A: 네, Dashboard에서 여러 사용자 계정을 생성하여 각자 독립적으로 사용 가능합니다.

**Q: Android 앱을 여러 기기에 설치할 수 있나요?**
A: 네, 각 기기마다 다른 Device Name으로 등록하면 동시에 사용 가능합니다.

### 9.2 Agent

**Q: Agent 앱이 배터리를 많이 소모하나요?**
A: 백그라운드에서 30초마다 네트워크 요청을 하므로 일반 앱보다 배터리 소모가 있습니다. Wi-Fi 사용 및 배터리 최적화 해제를 권장합니다.

**Q: Agent가 자동으로 재시작되나요?**
A: 앱이 종료되면 수동으로 다시 실행해야 합니다. 향후 버전에서 자동 재시작 기능 추가 예정입니다.

**Q: Android 버전 요구사항은?**
A: Android 8.0 (Oreo) 이상 권장합니다.

### 9.3 Job

**Q: Job 처리 시간은 얼마나 걸리나요?**
A: 평균 2-3분이며, 스크립트 길이와 기기 성능에 따라 다릅니다.

**Q: 한 번에 여러 Job을 생성할 수 있나요?**
A: 네, 원하는 만큼 생성 가능합니다. Agent는 우선순위 순서로 순차 처리합니다.

**Q: Job을 예약할 수 있나요?**
A: 현재 버전에서는 지원하지 않습니다. 향후 예약 게시 기능 추가 예정입니다.

### 9.4 게시

**Q: YouTube Shorts가 아닌 일반 영상으로 올릴 수 있나요?**
A: 현재는 Shorts 형식만 지원합니다.

**Q: 게시한 영상을 수정할 수 있나요?**
A: 게시 후에는 YouTube Studio 또는 TikTok 앱에서 직접 수정해야 합니다.

**Q: 공개 상태를 바로 Public으로 설정할 수 있나요?**
A: 현재는 Private로 업로드 후 YouTube Studio에서 수동 변경해야 합니다. 향후 옵션 추가 예정입니다.

### 9.5 보안

**Q: 내 YouTube/TikTok 계정이 안전한가요?**
A: OAuth 및 쿠키 인증은 안전하게 암호화되어 저장됩니다. 그러나 테스트용 계정 사용을 권장합니다.

**Q: 비밀번호는 어떻게 저장되나요?**
A: bcrypt 해싱으로 암호화되어 저장되며, 원본 비밀번호는 복구 불가능합니다.

**Q: 다른 사용자의 Job을 볼 수 있나요?**
A: 아니오, 각 사용자는 자신의 데이터만 볼 수 있습니다.

### 9.6 트러블슈팅

**Q: 시스템이 갑자기 작동하지 않아요.**
A: START-UAT.bat을 다시 실행하여 모든 서비스를 재시작하세요.

**Q: 에러 메시지를 어디서 확인할 수 있나요?**
A:
- Backend 로그: `admin/backend/logs/app.log`
- Frontend 콘솔: 브라우저 개발자 도구 (F12)
- Android 로그: Android Studio Logcat

**Q: 데이터가 삭제되었어요.**
A: PostgreSQL 데이터베이스를 백업하지 않았다면 복구 불가능합니다. 정기적인 백업을 권장합니다.

---

## 📞 지원 및 문의

### 기술 지원
- **이메일**: support@example.com
- **이슈 트래커**: https://github.com/your-repo/issues
- **문서**: 본 메뉴얼 및 `docs/` 폴더

### 피드백
- 기능 제안 및 버그 리포트는 이슈 트래커에 등록해주세요.
- 사용 중 불편한 점이나 개선 사항을 알려주세요.

---

**문서 버전**: 1.0  
**최종 업데이트**: 2026년 3월 3일  
**저작권**: © 2026 쇼츠 영상 자동화 플랫폼
