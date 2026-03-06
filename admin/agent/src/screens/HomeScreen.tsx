/**
 * 홈 화면 - Agent 상태 모니터링 및 Job 처리
 */

import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import type {NativeStackScreenProps} from '@react-navigation/native-stack';
import type {RootStackParamList} from '../App';
import DeviceInfo from 'react-native-device-info';
import BackgroundService from '@services/BackgroundService';
import ApiClient from '@services/ApiClient';
import VideoPipelineService from '@services/VideoPipelineService';
import type {Job, Agent} from '@app-types/api';

type Props = NativeStackScreenProps<RootStackParamList, 'Home'> & {
  onLogout: () => void;
};

const HomeScreen: React.FC<Props> = ({navigation, onLogout}) => {
  const [agent, setAgent] = useState<Agent | null>(null);
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [isServiceRunning, setIsServiceRunning] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAgentInfo();
    initializeBackgroundService();

    return () => {
      BackgroundService.stop();
    };
  }, []);

  const loadAgentInfo = async () => {
    try {
      const deviceId = await DeviceInfo.getUniqueId();
      const response = await ApiClient.getAgent(deviceId);
      
      if (response.data) {
        setAgent(response.data);
      }
    } catch (error) {
      console.error('Load agent info error:', error);
    }
  };

  const initializeBackgroundService = async () => {
    await BackgroundService.initialize(handleJobReceived);
    BackgroundService.start();
    setIsServiceRunning(true);
  };

  const handleJobReceived = async (job: Job) => {
    console.log('[HomeScreen] Job received:', job.id);
    setCurrentJob(job);

    try {
      await ApiClient.updateJobStatus(job.id, {
        status: 'rendering',
      });

      const renderResult = await VideoPipelineService.renderVideo(job);

      await ApiClient.updateJobStatus(job.id, {
        status: 'uploading',
        video_path: renderResult.videoPath,
      });

      const uploadResult = await VideoPipelineService.uploadVideo(job, renderResult.videoPath);

      await ApiClient.updateJobStatus(job.id, {
        status: 'completed',
        video_path: uploadResult.serverPath,
        video_url: uploadResult.videoUrl,
      });

      BackgroundService.jobCompleted();
      setCurrentJob(null);
      Alert.alert('성공', `Job #${job.id} 처리 완료\n영상 생성 및 등록 완료`);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown pipeline error';
      await handleJobFailed(job.id, message);
    }
  };

  const handleJobComplete = async (jobId: number) => {
    await ApiClient.updateJobStatus(jobId, {
      status: 'completed',
      video_path: '/storage/test_video.mp4',
    });

    BackgroundService.jobCompleted();
    setCurrentJob(null);
    Alert.alert('성공', 'Job이 완료되었습니다');
  };

  const handleJobFailed = async (jobId: number, error: string) => {
    await ApiClient.updateJobStatus(jobId, {
      status: 'failed',
      error_message: error,
    });

    BackgroundService.jobFailed();
    setCurrentJob(null);
    Alert.alert('실패', 'Job 처리에 실패했습니다');
  };

  const toggleService = () => {
    if (isServiceRunning) {
      BackgroundService.stop();
      setIsServiceRunning(false);
      Alert.alert('서비스 중지', 'Background 서비스가 중지되었습니다');
    } else {
      BackgroundService.start();
      setIsServiceRunning(true);
      Alert.alert('서비스 시작', 'Background 서비스가 시작되었습니다');
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAgentInfo();
    setRefreshing(false);
  };

  const handleLogoutPress = () => {
    Alert.alert('로그아웃', '로그아웃 하시겠습니까?', [
      {text: '취소', style: 'cancel'},
      {
        text: '로그아웃',
        style: 'destructive',
        onPress: () => {
          BackgroundService.stop();
          onLogout();
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }>
        {/* Agent 정보 */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Agent 정보</Text>
          {agent ? (
            <>
              <InfoRow label="Device ID" value={agent.device_id} />
              <InfoRow label="Device Name" value={agent.device_name} />
              <InfoRow
                label="상태"
                value={agent.status.toUpperCase()}
                valueColor={getStatusColor(agent.status)}
              />
              <InfoRow
                label="마지막 Heartbeat"
                value={new Date(agent.last_heartbeat).toLocaleString('ko-KR')}
              />
            </>
          ) : (
            <Text style={styles.noData}>Agent 정보를 불러오는 중...</Text>
          )}
        </View>

        {/* 서비스 상태 */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>서비스 상태</Text>
          <InfoRow
            label="Background Service"
            value={isServiceRunning ? '실행 중' : '중지'}
            valueColor={isServiceRunning ? '#10B981' : '#EF4444'}
          />
          <InfoRow
            label="처리 중인 Job"
            value={currentJob ? `#${currentJob.id}` : '없음'}
          />
        </View>

        {/* 현재 Job */}
        {currentJob && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>현재 Job</Text>
            <InfoRow label="Job ID" value={`#${currentJob.id}`} />
            <InfoRow label="제목" value={currentJob.title} />
            <InfoRow label="상태" value={currentJob.status.toUpperCase()} />
            <InfoRow label="언어" value={currentJob.source_language ?? 'ko'} />
            <Text style={styles.label}>내용</Text>
            <Text style={styles.jobContent}>{currentJob.script}</Text>
          </View>
        )}

        {/* 액션 버튼 */}
        <View style={styles.actions}>
          <TouchableOpacity
            style={[
              styles.button,
              isServiceRunning ? styles.buttonDanger : styles.buttonPrimary,
            ]}
            onPress={toggleService}>
            <Text style={styles.buttonText}>
              {isServiceRunning ? '서비스 중지' : '서비스 시작'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary]}
            onPress={() => navigation.navigate('Settings')}>
            <Text style={styles.buttonText}>설정</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.button, styles.buttonDanger]}
            onPress={handleLogoutPress}>
            <Text style={styles.buttonText}>로그아웃</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </View>
  );
};

const InfoRow: React.FC<{
  label: string;
  value: string;
  valueColor?: string;
}> = ({label, value, valueColor}) => (
  <View style={styles.infoRow}>
    <Text style={styles.label}>{label}</Text>
    <Text style={[styles.value, valueColor ? {color: valueColor} : undefined]}>
      {value}
    </Text>
  </View>
);

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'online':
      return '#10B981';
    case 'busy':
      return '#F59E0B';
    case 'offline':
      return '#6B7280';
    case 'error':
      return '#EF4444';
    default:
      return '#6B7280';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  scrollView: {
    flex: 1,
  },
  card: {
    backgroundColor: '#fff',
    margin: 16,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 12,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  label: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  value: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '600',
  },
  noData: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    paddingVertical: 20,
  },
  jobContent: {
    fontSize: 14,
    color: '#374151',
    marginTop: 8,
    lineHeight: 20,
  },
  actions: {
    padding: 16,
    paddingBottom: 32,
  },
  button: {
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 12,
  },
  buttonPrimary: {
    backgroundColor: '#4F46E5',
  },
  buttonSecondary: {
    backgroundColor: '#6B7280',
  },
  buttonDanger: {
    backgroundColor: '#EF4444',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default HomeScreen;
