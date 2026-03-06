/**
 * 메인 App 컴포넌트
 */

import React, {useEffect, useState} from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createNativeStackNavigator} from '@react-navigation/native-stack';
import type {NativeStackScreenProps} from '@react-navigation/native-stack';
import {SafeAreaProvider} from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

import HomeScreen from '@screens/HomeScreen';
import SettingsScreen from '@screens/SettingsScreen';
import LoginScreen from '@screens/LoginScreen';

export type RootStackParamList = {
  Home: undefined;
  Settings: undefined;
  Login: undefined;
};

type LoginScreenNavProps = NativeStackScreenProps<RootStackParamList, 'Login'>;
type HomeScreenNavProps = NativeStackScreenProps<RootStackParamList, 'Home'>;

const Stack = createNativeStackNavigator<RootStackParamList>();

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

  useEffect(() => {
    checkAuthentication();
  }, []);

  const checkAuthentication = async () => {
    try {
      const token = await AsyncStorage.getItem('jwt_token');
      setIsAuthenticated(!!token);
    } catch (error) {
      console.error('Check authentication error:', error);
      setIsAuthenticated(false);
    }
  };

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('jwt_token');
    setIsAuthenticated(false);
  };

  if (isAuthenticated === null) {
    // 로딩 중
    return null;
  }

  return (
    <SafeAreaProvider>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName={isAuthenticated ? 'Home' : 'Login'}
          screenOptions={{
            headerStyle: {
              backgroundColor: '#4F46E5',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}>
          {!isAuthenticated ? (
            <Stack.Screen name="Login" options={{headerShown: false}}>
              {(props: LoginScreenNavProps) => (
                <LoginScreen {...props} onLogin={handleLogin} />
              )}
            </Stack.Screen>
          ) : (
            <>
              <Stack.Screen
                name="Home"
                options={{title: 'Shorts Agent'}}>
                {(props: HomeScreenNavProps) => (
                  <HomeScreen {...props} onLogout={handleLogout} />
                )}
              </Stack.Screen>
              <Stack.Screen
                name="Settings"
                options={{title: '설정'}}
                component={SettingsScreen}
              />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </SafeAreaProvider>
  );
};

export default App;
