package com.shorts.agent

import android.os.Bundle
import com.facebook.react.ReactActivity
import com.facebook.react.ReactActivityDelegate
import com.facebook.react.defaults.DefaultNewArchitectureEntryPoint.fabricEnabled
import com.facebook.react.defaults.DefaultReactActivityDelegate

/**
 * MainActivity - React Native 진입점
 */
class MainActivity : ReactActivity() {

    /**
     * React Native 컴포넌트 이름 반환
     */
    override fun getMainComponentName(): String = "ShortsAgent"

    /**
     * React Activity Delegate 생성
     */
    override fun createReactActivityDelegate(): ReactActivityDelegate =
        DefaultReactActivityDelegate(this, mainComponentName, fabricEnabled)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Background Service 권한 요청 등의 초기화 작업
        // Phase 2에서 FFmpeg, 접근성 서비스 초기화 추가 예정
    }
}
