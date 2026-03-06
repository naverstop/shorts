/**
 * API 응답 타입 정의
 */

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

export interface Agent {
  id: number;
  user_id: number;
  device_id: string;
  device_name: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  last_heartbeat: string;
  current_job_id?: number;
  battery_level?: number;
  storage_available?: number;
  created_at: string;
}

export interface Job {
  id: number;
  user_id: number;
  title: string;
  script: string;
  status: 'pending' | 'assigned' | 'rendering' | 'uploading' | 'completed' | 'failed' | 'cancelled';
  agent_id?: number;
  target_platform_id: number;
  source_language?: string;
  target_languages?: string[];
  priority: number;
  retry_count: number;
  error_message?: string;
  video_path?: string;
  video_url?: string;
  created_at: string;
  assigned_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface Platform {
  id: number;
  name: string;
  code: string;
  is_active: boolean;
}

export interface HeartbeatData {
  device_id: string;
  status: 'online' | 'offline' | 'busy' | 'error';
  battery_level: number;
  storage_available: number;
  current_job_id?: number;
}

export interface JobStatusUpdate {
  status: 'pending' | 'assigned' | 'rendering' | 'uploading' | 'completed' | 'failed' | 'cancelled';
  error_message?: string;
  video_path?: string;
  video_url?: string;
}
