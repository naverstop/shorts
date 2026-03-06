# 실사용자 테스트 준비 가이드

## 📋 사전 준비 체크리스트

### 1. 필수 서비스 시작

#### 1.1 PostgreSQL (Docker)
```bash
cd c:/shorts
.\start-docker.bat
```
✅ 확인: `docker ps | grep postgres`

#### 1.2 Redis (Docker)
```bash
# Redis가 docker-compose.yml에 포함되어 있으면 자동 시작됨
# 없다면 별도 시작:
docker run -d -p 6379:6379 --name redis redis:7-alpine
```
✅ 확인: `docker ps | grep redis`

#### 1.3 Backend 서버
```bash
cd c:/shorts/admin/backend
# 가상환경 활성화
.\.venv\Scripts\Activate.ps1
# 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
✅ 확인: http://localhost:8001/health

#### 1.4 Celery Worker
새 터미널에서:
```bash
cd c:/shorts/admin/backend
.\.venv\Scripts\Activate.ps1
.\start-celery-worker.bat
```
✅ 확인: 로그에서 "celery@hostname ready" 확인

#### 1.5 Celery Beat (스케줄러)
새 터미널에서:
```bash
cd c:/shorts/admin/backend
.\.venv\Scripts\Activate.ps1
.\start-celery-beat.bat
```
✅ 확인: 로그에서 "beat: Starting..." 확인

#### 1.6 Celery Flower (선택적, 모니터링용)
새 터미널에서:
```bash
cd c:/shorts/admin/backend
.\.venv\Scripts\Activate.ps1
.\start-celery-flower.bat
```
✅ 확인: http://localhost:5555

#### 1.7 Frontend (빌드 후 서빙)
```bash
cd c:/shorts/admin/frontend
npm run build
npx serve -s dist -p 3000
```
✅ 확인: http://localhost:3000

---

## 🔐 2. Credential 설정

### 2.1 YouTube OAuth Credential

#### Google Cloud Console 설정
1. https://console.cloud.google.com 접속
2. 프로젝트 생성 또는 선택
3. "APIs & Services" → "Credentials"
4. "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Authorized redirect URIs:
   - `http://localhost:8001/api/v1/credentials/youtube/oauth-callback`
   - `http://localhost:3000/oauth-callback` (필요시)
7. Client ID 및 Client Secret 복사

#### 환경 변수 설정
`admin/backend/.env` 파일에 추가:
```env
YOUTUBE_CLIENT_ID=your_client_id_here
YOUTUBE_CLIENT_SECRET=your_client_secret_here
```

#### Dashboard에서 Credential 생성
1. http://localhost:3000 로그인
2. Credentials 섹션
3. "YouTube OAuth 시작" 버튼 클릭
4. Google 인증 창에서 로그인 및 권한 허용
5. Redirect된 페이지에서 `state`와 `code` 파라미터 복사
6. Dashboard의 OAuth 콜백 입력란에 붙여넣기
7. "OAuth 콜백 처리" 버튼 클릭

✅ 확인: Credentials 목록에 YouTube credential 표시

### 2.2 TikTok Credential (쿠키 기반)

#### 브라우저에서 쿠키 추출
1. Chrome/Edge 브라우저에서 https://www.tiktok.com 접속
2. 로그인 (테스트용 계정 사용)
3. 개발자 도구 (F12) → Application → Cookies → https://www.tiktok.com
4. 다음 쿠키들 복사:
   - `sessionid`
   - `tt_csrf_token`
   - `s_v_web_id`
   - `ttwid`

#### JSON 형식 변환
```json
[
  {
    "name": "sessionid",
    "value": "xxxxxxxxxxxxxxxxxxxxxxxx",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "tt_csrf_token",
    "value": "yyyyyyyyyyyyyyyyyyyy",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "s_v_web_id",
    "value": "zzzzzzzzzzzzzzzzzzzz",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  },
  {
    "name": "ttwid",
    "value": "aaaaaaaaaaaaaaaaaaaaa",
    "domain": ".tiktok.com",
    "path": "/",
    "secure": true
  }
]
```

#### Dashboard에서 Credential 생성
1. http://localhost:3000 로그인
2. Credentials 섹션
3. 플랫폼: TikTok 선택
4. Credential 이름: "TikTok Main Account" 입력
5. Credential JSON: 위의 JSON 전체 붙여넣기
6. "Credential 생성" 버튼 클릭

✅ 확인: Credentials 목록에 TikTok credential 표시

---

## 🎯 3. Playwright 브라우저 설치

TikTok 자동 게시를 위해 Playwright 브라우저 필요:

```bash
cd c:/shorts/admin/backend
.\.venv\Scripts\Activate.ps1
playwright install chromium
```

✅ 확인: `playwright show-trace` 실행 시 오류 없음

---

## 📱 4. Android Agent 준비

### 4.1 APK 빌드 (개발자용)
```bash
cd c:/shorts/admin/agent
npm install
npm run build:android
```
출력: `admin/agent/android/app/build/outputs/apk/release/app-release.apk`

### 4.2 Android 기기 설정
1. 개발자 옵션 활성화
2. USB 디버깅 허용
3. APK 설치:
   ```bash
   adb install admin/agent/android/app/build/outputs/apk/release/app-release.apk
   ```

### 4.3 앱 설정
1. 앱 실행
2. Settings에서 Backend URL 입력: `http://[PC_IP]:8001`
3. Device Name 입력 (예: "Test Phone 1")
4. "Register" 버튼 클릭

✅ 확인: Dashboard의 Agents 섹션에 Agent 표시

---

## 🧪 5. 실사용자 테스트 시나리오

### 시나리오 1: Android Agent Job 처리 (30분)

#### 사전 조건
- Android 기기 Agent 등록 완료
- Backend 서버 실행 중

#### 단계
1. **Job 생성** (Dashboard)
   - 플랫폼: YouTube
   - 제목: "Test Video from Agent"
   - 스크립트: "This is a test video."
   - 우선순위: 5
   - "Job 생성" 버튼 클릭

2. **Agent Job 수신 확인** (Android 앱)
   - Home 화면에서 "Pending Jobs" 카운트 증가 확인
   - Job 상세 화면에서 제목/스크립트 확인

3. **자동 처리 대기** (30초 간격)
   - Agent가 자동으로 Job을 시작
   - 상태 변화: `pending` → `rendering` → `uploading` → `completed`

4. **결과 확인** (Dashboard)
   - Jobs 목록에서 해당 Job이 `completed` 상태
   - Job 상세 정보에서 `video_path` 확인
   - Backend 서버: `/storage/videos/` 폴더에 파일 존재 확인

5. **영상 다운로드 및 재생**
   - 브라우저에서 `http://localhost:8001/storage/videos/{filename}` 접속
   - 영상 재생 확인

✅ **성공 기준**: Agent가 Job을 자동으로 수신하여 영상 생성 및 업로드 완료

---

### 시나리오 2: YouTube 실제 게시 (15분)

#### 사전 조건
- YouTube OAuth Credential 설정 완료
- 완료된 Job (video_path 존재)
- 테스트용 YouTube 채널 준비

#### 단계
1. **Dashboard에서 게시** (Frontend)
   - Jobs 목록에서 `completed` 상태 Job 선택
   - Job 액션에서 "YouTube 게시" 버튼 클릭
   - 확인 다이얼로그: "게시하시겠습니까?" → 확인

2. **Backend 처리 대기** (10-30초)
   - Backend 로그에서 YouTube Data API 호출 확인
   - `POST /api/v1/jobs/{id}/publish/youtube` 200 응답

3. **결과 확인** (Dashboard)
   - Job 상세 정보의 `job_metadata` 확인:
     ```json
     {
       "youtube_upload": {
         "video_id": "abc123xyz",
         "video_url": "https://www.youtube.com/watch?v=abc123xyz",
         "published_at": "2026-03-03T14:30:00Z"
       }
     }
     ```

4. **YouTube Studio 확인**
   - https://studio.youtube.com 접속
   - 콘텐츠 탭에서 업로드된 영상 확인
   - 제목/설명/태그 정합성 검증

5. **영상 시청**
   - `video_url` 링크 클릭
   - 영상 재생 확인 (공개 상태에 따라 다를 수 있음)

✅ **성공 기준**: YouTube에 영상이 정상적으로 업로드되고 URL 반환

---

### 시나리오 3: TikTok 실제 게시 (15분)

#### 사전 조건
- TikTok Credential (쿠키) 설정 완료
- Playwright 브라우저 설치
- 완료된 Job (video_path 존재)

#### 단계
1. **Dashboard에서 게시** (Frontend)
   - Jobs 목록에서 `completed` 상태 Job 선택
   - Job 액션에서 "TikTok 게시" 버튼 클릭

2. **Backend Playwright 실행 확인** (Backend 로그)
   ```
   INFO - Launching Playwright browser for TikTok upload
   INFO - Navigating to TikTok upload page
   INFO - Uploading video file...
   INFO - Filling caption...
   INFO - Clicking publish button
   INFO - TikTok upload completed
   ```

3. **TikTok 프로필 확인**
   - https://www.tiktok.com/@your_username 접속
   - 최근 업로드된 영상 확인
   - 캡션 및 해시태그 정합성 검증

4. **영상 재생 테스트**
   - 업로드된 영상 클릭
   - 재생 확인
   - 좋아요/댓글 기능 정상 동작 확인

✅ **성공 기준**: TikTok에 영상이 정상적으로 업로드되고 프로필에 표시

---

### 시나리오 4: Upload Quota 운영 검증 (20분)

#### 사전 조건
- 테스트 사용자 로그인
- YouTube 플랫폼 할당량 설정 (daily=2, weekly=10, monthly=30)

#### 단계
1. **할당량 생성** (Dashboard)
   - Upload Quotas 섹션
   - 플랫폼: YouTube
   - 일일: 2, 주간: 10, 월간: 30
   - "할당량 생성" 버튼 클릭

2. **할당량 확인**
   - 생성된 Quota 항목에서 "사용 0/0/0" 확인

3. **YouTube 게시 2회**
   - 시나리오 2를 2회 반복
   - 할당량이 "사용 2/2/2"로 업데이트 확인

4. **할당량 초과 테스트**
   - 3번째 YouTube 게시 시도
   - 에러 메시지 확인: "Daily limit exceeded"

5. **수동 리셋**
   - "Daily 초기화" 버튼 클릭
   - 확인 다이얼로그: "정말로 daily 할당량을 초기화하시겠습니까?" → 확인
   - 할당량이 "사용 0/2/2"로 업데이트 확인

6. **리셋 후 재시도**
   - 다시 YouTube 게시 시도
   - 정상적으로 게시 성공 확인

7. **자동 리셋 설정 확인** (Celery Beat)
   - `admin/backend/app/celery_app.py` 열기
   - `beat_schedule`에서 `reset_daily_quotas` 확인:
     ```python
     'reset_daily_quotas': {
         'task': 'app.tasks.cleanup.reset_daily_quotas',
         'schedule': crontab(hour=0, minute=0),  # 매일 00:00
     },
     ```

8. **Flower에서 스케줄 확인** (선택적)
   - http://localhost:5555 접속
   - "Tasks" 탭에서 `reset_daily_quotas` 확인

✅ **성공 기준**: 할당량 초과 시 업로드 차단, 수동 리셋 동작 확인

---

## 📊 6. 테스트 결과 기록

### 테스트 결과 시트

| 시나리오 | 담당자 | 시작 시각 | 종료 시각 | 결과 | 비고 |
|---------|-------|----------|----------|------|------|
| Android Agent Job 처리 | | | | ⏳ | |
| YouTube 실제 게시 | | | | ⏳ | |
| TikTok 실제 게시 | | | | ⏳ | |
| Upload Quota 운영 검증 | | | | ⏳ | |

### 이슈 기록 템플릿

**이슈 ID**: UAT-001  
**시나리오**: YouTube 실제 게시  
**심각도**: Critical / Major / Minor  
**설명**: (무엇이 잘못되었는지)  
**재현 단계**:
1. 
2. 
3. 

**예상 결과**: (무엇이 일어나야 하는지)  
**실제 결과**: (무엇이 일어났는지)  
**스크린샷/로그**: (첨부)  
**해결 방안**: (개발팀 기입)  

---

## 🚨 7. 트러블슈팅

### 문제 1: Agent가 Job을 수신하지 않음
**증상**: Android 앱에서 Job이 표시되지 않음

**확인 사항**:
1. Backend 서버가 실행 중인지: `http://localhost:8001/health`
2. Agent가 등록되었는지: Dashboard Agents 섹션 확인
3. Agent heartbeat가 전송되는지: Backend 로그 확인
4. Job 상태가 `pending`인지: Dashboard Jobs 섹션 확인

**해결 방법**:
- Agent 앱 재시작
- Backend URL 설정 확인
- 방화벽/네트워크 설정 확인

---

### 문제 2: YouTube 게시 실패 (401 Unauthorized)
**증상**: "Failed to publish to YouTube: 401 Unauthorized"

**확인 사항**:
1. YouTube OAuth Credential이 생성되었는지
2. Access Token이 만료되지 않았는지
3. YouTube Data API가 활성화되었는지

**해결 방법**:
- Dashboard에서 OAuth 재인증
- Google Cloud Console에서 API 활성화 확인
- Credential을 삭제하고 다시 생성

---

### 문제 3: TikTok 게시 실패 (쿠키 만료)
**증상**: "TikTok upload failed: Invalid session"

**확인 사항**:
1. TikTok 쿠키가 최신인지
2. Playwright 브라우저가 설치되었는지

**해결 방법**:
- 브라우저에서 다시 로그인하여 쿠키 추출
- Credential 업데이트
- `playwright install chromium` 재실행

---

### 문제 4: Celery Worker가 Task를 수행하지 않음
**증상**: Dashboard에서 "트렌드 수집" 버튼 클릭 후 반응 없음

**확인 사항**:
1. Celery Worker가 실행 중인지
2. Redis가 실행 중인지
3. Worker 로그에서 에러 확인

**해결 방법**:
- Redis 시작: `docker start redis`
- Worker 재시작: `.\start-celery-worker.bat`
- Flower에서 Task 상태 확인: http://localhost:5555

---

## ✅ 8. 최종 체크리스트

실사용자 테스트 시작 전 모든 항목 확인:

- [ ] PostgreSQL 실행 중
- [ ] Redis 실행 중
- [ ] Backend 서버 실행 중 (http://localhost:8001/health → status: healthy)
- [ ] Celery Worker 실행 중
- [ ] Celery Beat 실행 중
- [ ] Frontend 빌드 및 서빙 (http://localhost:3000)
- [ ] YouTube OAuth Credential 설정 완료
- [ ] TikTok Credential (쿠키) 설정 완료
- [ ] Playwright 브라우저 설치 완료
- [ ] Android APK 빌드 및 설치 완료 (선택적)
- [ ] 테스트용 계정 생성 및 로그인 확인
- [ ] 테스트 결과 기록 시트 준비

---

**준비 완료 시**: 실사용자 테스트 진행
**문제 발생 시**: 트러블슈팅 섹션 참고 또는 개발팀 문의
