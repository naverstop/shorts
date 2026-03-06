/**
 * API 클라이언트
 * Admin Server와 통신하는 모든 API 호출을 처리합니다.
 */

import axios, {AxiosInstance, AxiosError} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import RNFS from 'react-native-fs';
import {API_BASE_URL, API_TIMEOUT} from '@constants/config';
import type {
  ApiResponse,
  Agent,
  Job,
  HeartbeatData,
  JobStatusUpdate,
} from '@app-types/api';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request 인터셉터: JWT 토큰 자동 추가
    this.client.interceptors.request.use(
      async config => {
        if (!this.token) {
          this.token = await AsyncStorage.getItem('jwt_token');
        }
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      error => Promise.reject(error),
    );

    // Response 인터셉터: 에러 처리
    this.client.interceptors.response.use(
      response => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // 토큰 만료 처리
          await AsyncStorage.removeItem('jwt_token');
          this.token = null;
          console.error('JWT 토큰 만료. 재로그인 필요');
        }
        return Promise.reject(error);
      },
    );
  }

  async getToken(): Promise<string | null> {
    if (!this.token) {
      this.token = await AsyncStorage.getItem('jwt_token');
    }
    return this.token;
  }

  /**
   * JWT 토큰 설정
   */
  async setToken(token: string): Promise<void> {
    this.token = token;
    await AsyncStorage.setItem('jwt_token', token);
  }

  /**
   * 로그인
   */
  async login(username: string, password: string): Promise<ApiResponse<{access_token: string; token_type: string}>> {
    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await this.client.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.data.access_token) {
        await this.setToken(response.data.access_token);
      }

      return {data: response.data};
    } catch (error) {
      console.error('Login error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * Agent 등록 (디바이스 등록)
   */
  async registerAgent(deviceId: string, deviceName: string): Promise<ApiResponse<Agent>> {
    try {
      const response = await this.client.post('/agents', {
        device_id: deviceId,
        device_name: deviceName,
        status: 'online',
      });
      return {data: response.data};
    } catch (error) {
      console.error('Register agent error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * Heartbeat 전송
   */
  async sendHeartbeat(data: HeartbeatData): Promise<ApiResponse<void>> {
    try {
      await this.client.post('/agents/heartbeat', data);
      return {};
    } catch (error) {
      console.error('Heartbeat error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * 할당된 Job 조회 (Polling)
   */
  async getAssignedJob(deviceId: string): Promise<ApiResponse<Job | null>> {
    try {
      const response = await this.client.get('/jobs', {
        params: {
          status: 'assigned',
          device_id: deviceId,
        },
      });

      const jobs = response.data as Job[];
      return {data: jobs.length > 0 ? jobs[0] : null};
    } catch (error) {
      console.error('Get assigned job error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * Job 상태 업데이트
   */
  async updateJobStatus(
    jobId: number,
    update: JobStatusUpdate,
  ): Promise<ApiResponse<Job>> {
    try {
      const response = await this.client.patch(`/jobs/${jobId}/status`, update);
      return {data: response.data};
    } catch (error) {
      console.error('Update job status error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  async reportJobResult(
    jobId: number,
    videoPath: string,
    videoUrl?: string,
  ): Promise<ApiResponse<Job>> {
    return this.updateJobStatus(jobId, {
      status: 'completed',
      video_path: videoPath,
      video_url: videoUrl,
    });
  }

  async uploadJobVideo(jobId: number, filePath: string): Promise<ApiResponse<{video_path: string; video_url: string}>> {
    try {
      const token = await this.getToken();
      if (!token) {
        return {error: 'JWT token not found'};
      }

      const uploadResult = await RNFS.uploadFiles({
        toUrl: `${API_BASE_URL}/jobs/${jobId}/upload-video`,
        files: [
          {
            name: 'video',
            filename: `job_${jobId}.mp4`,
            filepath: filePath,
            filetype: 'video/mp4',
          },
        ],
        headers: {
          Authorization: `Bearer ${token}`,
        },
        method: 'POST',
      }).promise;

      if (uploadResult.statusCode < 200 || uploadResult.statusCode >= 300) {
        return {error: `Upload failed: HTTP ${uploadResult.statusCode}`};
      }

      const data = JSON.parse(uploadResult.body) as {video_path: string; video_url: string};
      return {data};
    } catch (error) {
      console.error('Upload job video error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * Job 상세 조회
   */
  async getJob(jobId: number): Promise<ApiResponse<Job>> {
    try {
      const response = await this.client.get(`/jobs/${jobId}`);
      return {data: response.data};
    } catch (error) {
      console.error('Get job error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * Agent 정보 조회
   */
  async getAgent(deviceId: string): Promise<ApiResponse<Agent>> {
    try {
      const response = await this.client.get('/agents', {
        params: {device_id: deviceId},
      });
      const agents = response.data as Agent[];
      if (agents.length === 0) {
        return {error: 'Agent not found'};
      }
      return {data: agents[0]};
    } catch (error) {
      console.error('Get agent error:', error);
      return {error: this._getErrorMessage(error)};
    }
  }

  /**
   * 에러 메시지 추출
   */
  private _getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
      return error.response?.data?.detail || error.message;
    }
    if (error instanceof Error) {
      return error.message;
    }
    return 'Unknown error';
  }
}

export default new ApiClient();
