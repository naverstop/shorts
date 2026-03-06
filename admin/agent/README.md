# Shorts Agent - Android Application

AI 기반 쇼츠 자동 생성 및 업로드를 수행하는 Android Agent 애플리케이션입니다.

## 📋 개요

이 앱은 Admin Server로부터 작업(Job)을 받아 영상을 자동으로 생성하고 플랫폼에 업로드하는 Agent 역할을 합니다.

### Phase 1 구현 내용 (Sprint 9-10주)

- ✅ **React Native + Kotlin Hybrid 구조**
- ✅ **Admin API 연동** (JWT 인증, OkHttp)
- ✅ **Heartbeat 시스템** (30초마다 상태 전송)
- ✅ **Job Polling** (30초마다 할당된 작업 확인)
- ✅ **로그인/등록 화면**
- ✅ **실시간 Agent 모니터링 화면**
- ✅ **기본 Job 자동 처리 파이프라인** (수신 → 렌더링 생성 → 백엔드 업로드 → 완료 보고)

### 예정 기능

- **Phase 2 (Sprint 11-12)**: FFmpeg 고도화/TTS/자막 동기화
- **Phase 3 (Sprint 13-14)**: 접근성 서비스를 통한 실제 플랫폼 업로드

## 🚀 시작하기

### 사전 요구사항

- Node.js 18+
- React Native CLI
- Android Studio
- JDK 17
- Android SDK (API 24+)

### 설치

```bash
# 의존성 설치
npm install

# iOS (macOS 전용)
cd ios && pod install && cd ..
```

### 개발 서버 실행

```bash
# Metro 번들러 시작
npm start

# Android 실행
npm run android

# iOS 실행 (macOS)
npm run ios
```

## 🏗️ 프로젝트 구조

```
agent/
├── android/                      # Android Native
│   ├── app/
│   │   ├── src/main/
│   │   │   ├── java/com/shorts/agent/
│   │   │   │   ├── MainActivity.kt
│   │   │   │   └── MainApplication.kt
│   │   │   └── AndroidManifest.xml
│   │   └── build.gradle
│   └── build.gradle
├── src/                          # React Native
│   ├── App.tsx                   # 메인 App
│   ├── constants/
│   │   └── config.ts             # API URL, 상수
│   ├── types/
│   │   └── api.ts                # TypeScript 타입
│   ├── services/
│   │   ├── ApiClient.ts          # Admin API 클라이언트
│   │   └── BackgroundService.ts  # Heartbeat & Polling
│   └── screens/
│       ├── LoginScreen.tsx       # 로그인 화면
│       ├── HomeScreen.tsx        # 메인 모니터링 화면
│       └── SettingsScreen.tsx    # 설정 화면
├── package.json
├── tsconfig.json
└── README.md
```

## ⚙️ 설정

### Admin Server URL 변경

앱 내 **설정 화면**에서 Admin Server URL을 변경할 수 있습니다.

기본값: `http://192.168.0.100:8001/api/v1`

### 로그인

Admin Server에 등록된 계정으로 로그인하세요. 로그인 시 자동으로 Agent가 등록됩니다.

## 🔧 주요 기능

### 1. Heartbeat 시스템

30초마다 Agent 상태를 Admin Server에 전송합니다:

- Device ID
- 상태 (online/busy/offline/error)
- 배터리 레벨
- 사용 가능한 저장 공간
- 현재 처리 중인 Job ID

### 2. Job Polling

30초마다 Admin Server에서 할당된 Job을 확인합니다. Job이 할당되면:

1. Job 상태를 'rendering'으로 업데이트
2. FFmpeg(가능 시)로 로컬 mp4 생성, 불가 시 fallback 파일 생성
3. Job 상태를 'uploading'으로 업데이트
4. 백엔드 업로드 API로 실제 파일 전송
5. Job 상태를 'completed'로 보고(video_path/video_url 포함)

> 참고: 현재 업로드는 백엔드 저장까지 실제 연동되며, SNS 플랫폼(YouTube/TikTok) 실제 게시는 Phase 3에서 구현됩니다.

### 3. Background Service

앱이 백그라운드에 있어도 Heartbeat와 Polling이 계속 실행됩니다.

## 📱 화면 구성

### 로그인 화면

- Admin Server 계정으로 로그인
- 자동 Agent 등록

### 홈 화면

- Agent 정보 (Device ID, 상태, 마지막 Heartbeat)
- 서비스 상태 (Background Service 실행 여부)
- 현재 처리 중인 Job 정보
- 서비스 시작/중지 버튼

### 설정 화면

- Admin Server URL 변경
- 디바이스 정보 확인
- 저장소 경로 확인

## 🔐 보안

- JWT 토큰 기반 인증
- AsyncStorage에 토큰 안전하게 저장
- HTTPS 통신 (프로덕션)

## 🐛 디버깅

### React Native Debugger

```bash
# Chrome DevTools
npm start
# Press 'j' to open debugger
```

### Android Logcat

```bash
adb logcat | grep "ShortsAgent"
```

## 📦 빌드

### Debug APK

```bash
cd android
./gradlew assembleDebug
```

APK 위치: `android/app/build/outputs/apk/debug/app-debug.apk`

### Release APK

```bash
cd android
./gradlew assembleRelease
```

## 🚧 개발 로드맵

### Phase 1 - API 통신 (완료)

- ✅ Heartbeat 시스템
- ✅ Job Polling
- ✅ Agent 등록/관리
- ✅ 기본 UI

### Phase 2 - 영상 렌더링 (Sprint 11-12)

- [ ] FFmpeg 고도화 (현재 기본 렌더링 + fallback)
- [ ] TTS 음성 합성
- [ ] 자막 타이밍 동기화
- [ ] 최종 영상 생성

### Phase 3 - 자동 업로드 (Sprint 13-14)

- [ ] Accessibility Service
- [ ] YouTube Shorts 자동 업로드
- [ ] TikTok 자동 업로드
- [ ] 업로드 결과 Admin Server 전송 (현재 completed/video_path/video_url 기본 보고만 구현)

## 📖 참고 자료

- [React Native 공식 문서](https://reactnative.dev/)
- [Kotlin 공식 문서](https://kotlinlang.org/docs/home.html)
- [Admin Server API 문서](http://localhost:8001/docs)

## 📄 라이선스

© 2026 Shorts Generator. All rights reserved.

---

**작성일**: 2026-03-02  
**버전**: 1.0.0  
**Phase**: Phase 1 (Sprint 9-10)
