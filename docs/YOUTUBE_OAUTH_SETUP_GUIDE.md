# YouTube OAuth2 설정 가이드

**작성일**: 2026년 3월 4일  
**목적**: OAuth "401 오류: invalid_client" 문제 해결

---

## 🚨 현재 문제

YouTube OAuth 시작 버튼 클릭 시 다음 오류 발생:
```
액세스 차단됨: 승인 오류
이 앱의 개발자가 앱을 올바르게 설정하지 않았기 때문에 앱이 Google 로그인을 사용할 수 없습니다.

401 오류: invalid_client
```

**원인**: Google Cloud Console의 OAuth 클라이언트 설정 문제

---

## ✅ 해결 방법

### 1단계: Google Cloud Console 접속

1. https://console.cloud.google.com 접속
2. 프로젝트 선택 (또는 새 프로젝트 생성)
3. 좌측 메뉴에서 **"API 및 서비스" > "사용자 인증 정보"** 클릭

---

### 2단계: OAuth 동의 화면 설정 확인

1. 좌측 메뉴에서 **"OAuth 동의 화면"** 클릭
2. 설정 확인:
   - **사용자 유형**: "외부" 선택 (개인 계정용)
   - **앱 이름**: `AI Shorts Generator` (또는 원하는 이름)
   - **사용자 지원 이메일**: 본인 이메일
   - **개발자 연락처**: 본인 이메일
3. **"저장 후 계속"** 클릭

#### 범위(Scope) 추가
1. **"범위 추가 또는 삭제"** 클릭
2. 다음 3개 범위 추가:
   - `https://www.googleapis.com/auth/youtube.upload` (영상 업로드)
   - `https://www.googleapis.com/auth/youtube` (채널 관리)
   - `https://www.googleapis.com/auth/youtube.readonly` (채널 정보 읽기)
3. **"저장 후 계속"** 클릭

#### 테스트 사용자 추가 (외부 모드인 경우)
1. **"테스트 사용자 추가"** 클릭
2. 본인 Gmail 주소 입력
3. **"저장 후 계속"** 클릭

---

### 3단계: OAuth 2.0 클라이언트 ID 확인/생성

#### 3-1. 기존 클라이언트 확인

1. **"사용자 인증 정보"** 탭으로 돌아가기
2. **"OAuth 2.0 클라이언트 ID"** 섹션 확인
3. 다음 클라이언트가 있는지 확인:
   ```
   클라이언트 ID: YOUR_CLIENT_ID.apps.googleusercontent.com
   ```

#### 3-2. 클라이언트가 없는 경우 (새로 생성)

1. **"사용자 인증 정보 만들기" > "OAuth 클라이언트 ID"** 클릭
2. 애플리케이션 유형: **"웹 애플리케이션"** 선택
3. 이름: `AI Shorts Generator - Web` 입력

4. **승인된 JavaScript 원본** 추가:
   ```
   http://localhost:3000
   http://localhost:8001
   ```

5. **승인된 리디렉션 URI** 추가 (중요!):
   ```
   http://localhost:8001/api/v1/oauth/youtube/callback
   ```

6. **"만들기"** 클릭

7. 생성된 클라이언트 ID와 클라이언트 보안 비밀번호 복사

#### 3-3. 기존 클라이언트 수정

1. 클라이언트 이름 오른쪽의 **"편집"** 아이콘 (연필) 클릭
2. **"승인된 리디렉션 URI"** 섹션 확인
3. 다음 URI가 있는지 확인 (없으면 추가):
   ```
   http://localhost:8001/api/v1/oauth/youtube/callback
   ```
4. **"저장"** 클릭

---

### 4단계: .env 파일 업데이트 (필요한 경우)

`c:\shorts\admin\backend\.env` 파일 열기:

```env
# YouTube OAuth2 Client (사용자별 업로드용)
YOUTUBE_CLIENT_ID=YOUR_CLIENT_ID.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=YOUR_CLIENT_SECRET
OAUTH_REDIRECT_URI=http://localhost:8001/api/v1/oauth/youtube/callback
```

**새로 생성한 경우**: 위 값들을 Google Cloud Console에서 복사한 값으로 교체

---

### 5단계: YouTube Data API 활성화

1. 좌측 메뉴에서 **"라이브러리"** 클릭
2. "YouTube Data API v3" 검색
3. **"사용 설정"** 클릭 (이미 활성화된 경우 "관리" 버튼)

---

### 6단계: Backend 재시작

설정 변경 후 Backend 서버 재시작 필요:

```powershell
# c:\shorts 디렉토리에서
.\START.bat
```

또는 개별 서비스 재시작:

```powershell
cd c:\shorts\admin\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

---

## 🔍 설정 확인 체크리스트

다음 항목들을 모두 확인하세요:

- [ ] **OAuth 동의 화면 설정 완료**
  - 앱 이름 설정
  - 사용자 지원 이메일 설정
  - 3개 범위(Scope) 추가
  - 테스트 사용자 추가 (본인 Gmail)

- [ ] **OAuth 클라이언트 ID 설정 확인**
  - 승인된 리디렉션 URI: `http://localhost:8001/api/v1/oauth/youtube/callback`
  - (선택) 승인된 JavaScript 원본: `http://localhost:3000`, `http://localhost:8001`

- [ ] **YouTube Data API v3 활성화**

- [ ] **.env 파일 설정 확인**
  - `YOUTUBE_CLIENT_ID`: Google Cloud Console의 클라이언트 ID
  - `YOUTUBE_CLIENT_SECRET`: Google Cloud Console의 클라이언트 보안 비밀번호
  - `OAUTH_REDIRECT_URI`: `http://localhost:8001/api/v1/oauth/youtube/callback`

- [ ] **Backend 재시작**

---

## 🧪 테스트 방법

### 1. Dashboard 접속
1. http://localhost:3000 접속
2. testadmin / admin123 로그인

### 2. YouTube OAuth 테스트
1. 좌측 메뉴에서 **"플랫폼 관리"** 클릭
2. **YouTube** 카드 클릭
3. **인증 정보** 섹션에서 **"OAuth 시작"** 버튼 클릭
4. 새 창이 열리며 Google 로그인 화면 표시되어야 함

### 3. 예상 동작
- ✅ Google 로그인 화면 정상 표시
- ✅ "AI Shorts Generator가 다음을 요청함" 동의 화면 표시
- ✅ 승인 후 콜백 페이지로 리디렉션
- ✅ URL에 `code=...&state=...` 파라미터 포함

### 4. 여전히 401 오류 발생 시
다음을 확인:
1. Google Cloud Console에서 **리디렉션 URI가 정확히** `http://localhost:8001/api/v1/oauth/youtube/callback`인지 확인
2. **OAuth 동의 화면 → 게시 상태**가 "테스트" 또는 "프로덕션"인지 확인
3. **테스트 사용자 목록**에 본인 Gmail이 추가되어 있는지 확인
4. 브라우저 캐시 삭제 후 재시도

---

## 📌 주의사항

### 개발 환경 (localhost)
- 리디렉션 URI: `http://localhost:8001/api/v1/oauth/youtube/callback`
- HTTPS 불필요

### 프로덕션 환경 (도메인)
- 리디렉션 URI: `https://yourdomain.com/api/v1/oauth/youtube/callback`
- **반드시 HTTPS 사용**
- Google Cloud Console에서 프로덕션 URI 별도 추가 필요

### OAuth 동의 화면 게시 상태
- **테스트 모드**: 테스트 사용자 최대 100명까지 (개발용)
- **프로덕션 모드**: Google 심사 필요 (일반 사용자용)

---

## 🔗 참고 자료

- [Google OAuth 2.0 문서](https://developers.google.com/identity/protocols/oauth2)
- [YouTube Data API 문서](https://developers.google.com/youtube/v3)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)

---

## 📞 추가 도움

문제가 계속되면 다음 정보를 제공해주세요:
1. Google Cloud Console 스크린샷 (OAuth 클라이언트 설정 부분)
2. OAuth 시작 버튼 클릭 시 브라우저 콘솔 에러
3. Backend 로그 (`c:\shorts\admin\backend\logs\app.log`)

---

**마지막 업데이트**: 2026년 3월 4일  
**버전**: 1.0
