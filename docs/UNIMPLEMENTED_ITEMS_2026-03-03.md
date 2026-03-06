# 미개발 항목 정의 (2026-03-03)

## 기준
- 기준 브랜치: 현재 `c:\shorts` 워크스페이스 코드 상태
- 분류 원칙:
  - **미개발**: 기능 경로/핵심 로직 자체가 없음
  - **부분개발**: 엔드포인트/화면은 있으나 실연동 또는 운영수준 미완

## A. 미개발

1) 관리자 콘솔 운영 화면 고도화
- 범위: Quota 고급 필터/삭제/리셋/권한 기반 세부 제어
- 상태: 기본 Quota 생성/조회/상향 UI는 반영됨
- 위치: `admin/frontend/src/pages/DashboardPage.tsx`

## B. 부분개발

1) Agent-Backend API 계약 정합
- 기존 문제:
  - Agent heartbeat: `POST /agents/heartbeat` (device_id 기반)
  - Backend heartbeat: `POST /agents/{agent_id}/heartbeat`
  - Agent job status: `PATCH /jobs/{id}/status`
  - Backend job status: `POST /jobs/{id}/status`
  - Agent assigned job 조회: `status`, `device_id` 쿼리 사용
- 오늘 반영 내용:
  - `POST /api/v1/agents/heartbeat` 호환 엔드포인트 추가
  - `GET /api/v1/agents`에 `device_id` 필터 추가
  - `GET /api/v1/jobs`에 `status`(alias), `device_id` 필터 추가
  - `PATCH /api/v1/jobs/{job_id}/status` alias 추가

2) Celery Phase 1.5 정기작업
- 기존 문제: trends/stats 스케줄이 주석 처리
- 오늘 반영 내용: `ENABLE_PHASE15_TASKS` 환경변수로 안전하게 활성화 가능
  - collect_youtube_trends (매시)
  - collect_tiktok_trends (매시 30분)
  - sync_video_stats (6시간)
  - analyze_video_performance (매일 03:30)
  - check_agent_disk_usage (매일 04:30)

3) 테스트 인프라
- 상태: `tests/conftest.py`의 `test_db` fixture TODO
- 영향: 통합 테스트 신뢰성/독립성 저하

4) Android 주문접수→영상생성→등록 파이프라인
- 반영 상태: **부분개발(실제 업로드 연동 포함)**
- 동작 흐름:
  - Job 수신 시 `rendering` 업데이트
  - FFmpeg 렌더링 시도(가능 시 실제 mp4 생성, 불가 시 fallback)
  - `uploading` 업데이트 후 백엔드 업로드 API로 실제 파일 전송
  - `completed` + `video_path/video_url` 등록
- 구현 위치:
  - `admin/agent/src/services/VideoPipelineService.ts`
  - `admin/agent/src/services/ApiClient.ts` (`uploadJobVideo`)
  - `admin/agent/src/screens/HomeScreen.tsx`
  - `admin/backend/app/schemas.py` (`JobStatusUpdate` video fields)
  - `admin/backend/app/routes/jobs.py` (`POST /api/v1/jobs/{job_id}/upload-video`)
  - `admin/backend/app/main.py` (`/storage/videos` 정적 제공)
- 남은 과제:
  - FFmpeg 렌더링 고도화(스크립트 자막/오디오 합성)
  - 업로드 결과 딥링크/메타 검증

5) YouTube 실제 게시 연동
- 반영 상태: **기본 동작 구현 완료(운영 자격증명 필요)**
- 구현 내용:
  - `POST /api/v1/jobs/{job_id}/publish/youtube` 추가
  - 완료된 Job의 `job_metadata.video_path` 파일을 YouTube Data API로 업로드
  - 업로드 성공 시 `job_metadata.youtube_upload`에 `video_id`, `video_url`, `published_at` 저장
  - Dashboard 완료 Job 액션에 `YouTube 게시` 버튼 추가
- 구현 위치:
  - `admin/backend/app/services/youtube_publish_service.py`
  - `admin/backend/app/routes/jobs.py`
  - `admin/backend/app/schemas.py`
  - `admin/frontend/src/services/api.ts`
  - `admin/frontend/src/pages/DashboardPage.tsx`
- 운영 전제:
  - YouTube OAuth credential(활성 상태) 필요
  - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, Redirect URI 설정 필요

6) TikTok 실제 게시/수집 연동
- 반영 상태: **기본 동작 구현 완료(운영 자격증명 필요)**
- 구현 내용:
  - `collect_tiktok_trends`에서 Playwright 기반 Discover 스크래핑 우선 적용
  - 스크래핑 실패 시 YouTube 기반 fallback 추정 유지
  - `POST /api/v1/jobs/{job_id}/publish/tiktok` 추가
  - Dashboard 완료 Job 액션에 `TikTok 게시` 버튼 추가
- 구현 위치:
  - `admin/backend/app/services/tiktok_trend_client.py`
  - `admin/backend/app/tasks/trends.py`
  - `admin/backend/app/services/tiktok_publish_service.py`
  - `admin/backend/app/routes/jobs.py`
  - `admin/frontend/src/services/api.ts`
  - `admin/frontend/src/pages/DashboardPage.tsx`
- 운영 전제:
  - TikTok credential에 `cookies_json` 필요 (브라우저 세션)
  - Playwright 런타임/브라우저 설치 필요

## C. 즉시 다음 개발 권장 순서
1. Agent 앱에서 실제 단말 E2E(잡 수신→생성→완료등록) 검증
2. FFmpeg 렌더링 고도화(스크립트 자막/오디오 합성)
3. 업로드 결과 딥링크/메타 검증 자동화
4. Celery worker/beat 운영 프로세스 검증 및 실패 알림 추가
5. TikTok/YouTube 운영 credential 관리 자동화
