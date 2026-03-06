/**
 * API 클라이언트 상수
 */

// Admin Server API Base URL (개발 환경)
export const API_BASE_URL = 'http://192.168.0.100:8001/api/v1';

// Polling 간격 (30초)
export const POLLING_INTERVAL = 30000;

// Heartbeat 전송 간격 (30초)
export const HEARTBEAT_INTERVAL = 30000;

// API 타임아웃 (30초)
export const API_TIMEOUT = 30000;

// Storage 경로
export const STORAGE_PATH = {
  VIDEOS: '/storage/emulated/0/ShortsAgent/videos',
  TEMP: '/storage/emulated/0/ShortsAgent/temp',
  LOGS: '/storage/emulated/0/ShortsAgent/logs',
};

// Job 상태
export const JOB_STATUS = {
  PENDING: 'pending',
  ASSIGNED: 'assigned',
  RENDERING: 'rendering',
  UPLOADING: 'uploading',
  COMPLETED: 'completed',
  FAILED: 'failed',
  CANCELLED: 'cancelled',
} as const;

// Agent 상태
export const AGENT_STATUS = {
  ONLINE: 'online',
  OFFLINE: 'offline',
  BUSY: 'busy',
  ERROR: 'error',
} as const;
