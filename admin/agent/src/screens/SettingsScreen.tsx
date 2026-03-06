/**
 * 설정 화면
 */

import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {API_BASE_URL} from '@constants/config';
import DeviceInfo from 'react-native-device-info';

const SettingsScreen: React.FC = () => {
  const [apiUrl, setApiUrl] = useState(API_BASE_URL);
  const [deviceInfo, setDeviceInfo] = useState({
    deviceId: '',
    deviceName: '',
    model: '',
    systemVersion: '',
    appVersion: '',
  });

  useEffect(() => {
    loadSettings();
    loadDeviceInfo();
  }, []);

  const loadSettings = async () => {
    try {
      const savedUrl = await AsyncStorage.getItem('api_url');
      if (savedUrl) {
        setApiUrl(savedUrl);
      }
    } catch (error) {
      console.error('Load settings error:', error);
    }
  };

  const loadDeviceInfo = async () => {
    const deviceId = await DeviceInfo.getUniqueId();
    const deviceName = await DeviceInfo.getDeviceName();
    const model = await DeviceInfo.getModel();
    const systemVersion = await DeviceInfo.getSystemVersion();
    const appVersion = await DeviceInfo.getVersion();

    setDeviceInfo({
      deviceId,
      deviceName,
      model,
      systemVersion,
      appVersion,
    });
  };

  const handleSaveUrl = async () => {
    try {
      await AsyncStorage.setItem('api_url', apiUrl);
      Alert.alert('저장 완료', 'API URL이 저장되었습니다.\n앱을 재시작해주세요.');
    } catch (error) {
      console.error('Save URL error:', error);
      Alert.alert('오류', 'API URL 저장에 실패했습니다');
    }
  };

  const handleResetUrl = () => {
    setApiUrl(API_BASE_URL);
  };

  return (
    <ScrollView style={styles.container}>
      {/* API 설정 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>API 설정</Text>
        <Text style={styles.label}>Admin Server URL</Text>
        <TextInput
          style={styles.input}
          value={apiUrl}
          onChangeText={setApiUrl}
          placeholder="http://192.168.0.100:8001/api/v1"
          autoCapitalize="none"
        />
        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.button, styles.buttonSecondary]}
            onPress={handleResetUrl}>
            <Text style={styles.buttonText}>초기화</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.button, styles.buttonPrimary]}
            onPress={handleSaveUrl}>
            <Text style={styles.buttonText}>저장</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* 디바이스 정보 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>디바이스 정보</Text>
        <InfoRow label="Device ID" value={deviceInfo.deviceId} />
        <InfoRow label="Device Name" value={deviceInfo.deviceName} />
        <InfoRow label="Model" value={deviceInfo.model} />
        <InfoRow label="Android Version" value={deviceInfo.systemVersion} />
        <InfoRow label="App Version" value={deviceInfo.appVersion} />
      </View>

      {/* 저장소 정보 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>저장소</Text>
        <Text style={styles.infoText}>
          영상 저장 경로:{'\n'}
          /storage/emulated/0/ShortsAgent/videos
        </Text>
        <Text style={styles.infoText}>
          임시 파일:{'\n'}
          /storage/emulated/0/ShortsAgent/temp
        </Text>
        <Text style={styles.infoText}>
          로그:{'\n'}
          /storage/emulated/0/ShortsAgent/logs
        </Text>
      </View>

      {/* 앱 정보 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>앱 정보</Text>
        <Text style={styles.infoText}>
          Shorts Agent v{deviceInfo.appVersion}
        </Text>
        <Text style={styles.infoText}>
          AI 기반 쇼츠 자동 생성 및 업로드 시스템
        </Text>
        <Text style={styles.copyright}>
          © 2026 Shorts Generator. All rights reserved.
        </Text>
      </View>
    </ScrollView>
  );
};

const InfoRow: React.FC<{label: string; value: string}> = ({label, value}) => (
  <View style={styles.infoRow}>
    <Text style={styles.infoLabel}>{label}</Text>
    <Text style={styles.infoValue}>{value}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  section: {
    backgroundColor: '#fff',
    margin: 16,
    marginBottom: 0,
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
    fontWeight: '500',
  },
  input: {
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#4F46E5',
  },
  buttonSecondary: {
    backgroundColor: '#6B7280',
  },
  buttonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  infoLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  infoValue: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '500',
  },
  infoText: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 8,
  },
  copyright: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default SettingsScreen;
