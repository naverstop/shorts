/**
 * 로그인 화면
 */

import React, {useState} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import DeviceInfo from 'react-native-device-info';
import ApiClient from '@services/ApiClient';

interface LoginScreenProps {
  onLogin: () => void;
}

const LoginScreen: React.FC<LoginScreenProps> = ({onLogin}) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('오류', '사용자명과 비밀번호를 입력하세요');
      return;
    }

    setLoading(true);

    try {
      // 1. 로그인
      const loginResponse = await ApiClient.login(username, password);
      
      if (loginResponse.error) {
        Alert.alert('로그인 실패', loginResponse.error);
        setLoading(false);
        return;
      }

      // 2. Agent 등록
      const deviceId = await DeviceInfo.getUniqueId();
      const deviceName = await DeviceInfo.getDeviceName();
      const model = await DeviceInfo.getModel();
      const fullDeviceName = `${deviceName} (${model})`;

      const registerResponse = await ApiClient.registerAgent(
        deviceId,
        fullDeviceName,
      );

      if (registerResponse.error && !registerResponse.error.includes('already exists')) {
        Alert.alert('Agent 등록 실패', registerResponse.error);
        setLoading(false);
        return;
      }

      // 로그인 성공
      onLogin();
    } catch (error) {
      console.error('Login error:', error);
      Alert.alert('오류', '로그인 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <View style={styles.content}>
        <Text style={styles.title}>Shorts Agent</Text>
        <Text style={styles.subtitle}>AI 쇼츠 자동 생성 에이전트</Text>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="사용자명"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            editable={!loading}
          />

          <TextInput
            style={styles.input}
            placeholder="비밀번호"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            editable={!loading}
          />

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={loading}>
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>로그인</Text>
            )}
          </TouchableOpacity>
        </View>

        <Text style={styles.footer}>
          Admin Server에 등록된 계정으로 로그인하세요
        </Text>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4F46E5',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginBottom: 40,
  },
  form: {
    width: '100%',
    maxWidth: 400,
  },
  input: {
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    marginBottom: 16,
  },
  button: {
    backgroundColor: '#4F46E5',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    marginTop: 24,
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
  },
});

export default LoginScreen;
