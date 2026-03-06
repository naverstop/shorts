/**
 * Background Service Manager
 * Heartbeat와 Job Polling 서비스를 관리합니다.
 */

import BackgroundTimer from 'react-native-background-timer';
import DeviceInfo from 'react-native-device-info';
import RNFS from 'react-native-fs';
import ApiClient from './ApiClient';
import {
  POLLING_INTERVAL,
  HEARTBEAT_INTERVAL,
  AGENT_STATUS,
} from '@constants/config';
import type {Job, HeartbeatData} from '@app-types/api';

class BackgroundService {
  private heartbeatTimerId: number | null = null;
  private pollingTimerId: number | null = null;
  private deviceId: string = '';
  private currentJobId: number | null = null;
  private isProcessing: boolean = false;
  private onJobReceived?: (job: Job) => Promise<void> | void;

  /**
   * 초기화
   */
  async initialize(onJobReceived: (job: Job) => Promise<void> | void): Promise<void> {
    this.deviceId = await DeviceInfo.getUniqueId();
    this.onJobReceived = onJobReceived;
    console.log('[BackgroundService] Initialized with deviceId:', this.deviceId);
  }

  /**
   * 서비스 시작
   */
  start(): void {
    console.log('[BackgroundService] Starting services...');
    this.startHeartbeat();
    this.startPolling();
  }

  /**
   * 서비스 중지
   */
  stop(): void {
    console.log('[BackgroundService] Stopping services...');
    if (this.heartbeatTimerId) {
      BackgroundTimer.clearInterval(this.heartbeatTimerId);
      this.heartbeatTimerId = null;
    }
    if (this.pollingTimerId) {
      BackgroundTimer.clearInterval(this.pollingTimerId);
      this.pollingTimerId = null;
    }
  }

  /**
   * Heartbeat 시작
   */
  private startHeartbeat(): void {
    // 즉시 한 번 전송
    this.sendHeartbeat();

    // 30초마다 Heartbeat 전송
    this.heartbeatTimerId = BackgroundTimer.setInterval(() => {
      this.sendHeartbeat();
    }, HEARTBEAT_INTERVAL);

    console.log('[BackgroundService] Heartbeat started');
  }

  /**
   * Heartbeat 전송
   */
  private async sendHeartbeat(): Promise<void> {
    try {
      const batteryLevel = await DeviceInfo.getBatteryLevel();
      const freeSpace = await RNFS.getFSInfo();
      const storageAvailableGB = Math.floor(freeSpace.freeSpace / (1024 * 1024 * 1024));

      const heartbeatData: HeartbeatData = {
        device_id: this.deviceId,
        status: this.isProcessing ? AGENT_STATUS.BUSY : AGENT_STATUS.ONLINE,
        battery_level: Math.floor(batteryLevel * 100),
        storage_available: storageAvailableGB,
        current_job_id: this.currentJobId || undefined,
      };

      await ApiClient.sendHeartbeat(heartbeatData);
      console.log('[BackgroundService] Heartbeat sent:', heartbeatData);
    } catch (error) {
      console.error('[BackgroundService] Heartbeat failed:', error);
    }
  }

  /**
   * Job Polling 시작
   */
  private startPolling(): void {
    // 즉시 한 번 확인
    this.checkForJob();

    // 30초마다 Job 확인
    this.pollingTimerId = BackgroundTimer.setInterval(() => {
      this.checkForJob();
    }, POLLING_INTERVAL);

    console.log('[BackgroundService] Polling started');
  }

  /**
   * 할당된 Job 확인
   */
  private async checkForJob(): Promise<void> {
    // 이미 작업 중이면 Skip
    if (this.isProcessing) {
      console.log('[BackgroundService] Already processing a job, skipping...');
      return;
    }

    try {
      const response = await ApiClient.getAssignedJob(this.deviceId);
      
      if (response.error) {
        console.error('[BackgroundService] Job polling error:', response.error);
        return;
      }

      if (response.data) {
        console.log('[BackgroundService] Job received:', response.data.id);
        this.currentJobId = response.data.id;
        this.isProcessing = true;

        // Job 처리 콜백 호출
        if (this.onJobReceived) {
          await Promise.resolve(this.onJobReceived(response.data));
        }
      }
    } catch (error) {
      console.error('[BackgroundService] Polling failed:', error);
    }
  }

  /**
   * Job 완료 처리
   */
  jobCompleted(): void {
    this.currentJobId = null;
    this.isProcessing = false;
    console.log('[BackgroundService] Job completed, ready for next job');
  }

  /**
   * Job 실패 처리
   */
  jobFailed(): void {
    this.currentJobId = null;
    this.isProcessing = false;
    console.log('[BackgroundService] Job failed, ready for next job');
  }

  /**
   * 현재 작업 중인 Job ID 반환
   */
  getCurrentJobId(): number | null {
    return this.currentJobId;
  }

  /**
   * 처리 중 여부 반환
   */
  isJobProcessing(): boolean {
    return this.isProcessing;
  }
}

export default new BackgroundService();
