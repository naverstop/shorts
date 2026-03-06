"""
Gemini AI Client
- 트렌드 분석
- 콘텐츠 구조 분석
"""
import os
from typing import Dict, List, Optional
from loguru import logger

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Gemini API disabled.")


class GeminiClient:
    """
    Google Gemini AI 클라이언트
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai is required.")
        
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment")
            return
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    async def analyze_trend(
        self,
        videos: List[Dict],
        language: str = "ko"
    ) -> Dict:
        """
        트렌드 분석
        
        Args:
            videos: YouTube 비디오 목록
            language: 분석 언어
        
        Returns:
            분석 결과 Dict
        """
        if not hasattr(self, 'model'):
            logger.error("Gemini API not initialized")
            return {}
        
        try:
            # 비디오 데이터 요약
            video_summaries = []
            for v in videos[:20]:  # 상위 20개만 분석
                video_summaries.append({
                    "title": v.get("title"),
                    "views": v.get("view_count"),
                    "likes": v.get("like_count"),
                    "tags": v.get("tags", [])[:5]  # 상위 5개 태그만
                })
            
            prompt = f"""
다음은 현재 인기있는 YouTube 비디오 목록입니다. 트렌드를 분석해주세요.

비디오 목록:
{video_summaries}

다음 형식의 JSON으로 응답해주세요:
{{
    "summary": "트렌드 요약 (100자 이내)",
    "main_topics": ["주요 토픽1", "주요 토픽2", "주요 토픽3"],
    "target_audience": ["타겟 청중1", "타겟 청중2"],
    "content_suggestions": ["콘텐츠 제안1", "콘텐츠 제안2", "콘텐츠 제안3"],
    "viral_potential": 85,
    "recommended_platforms": ["youtube", "tiktok"],
    "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}}

언어: {language}
"""
            
            response = self.model.generate_content(prompt)
            
            # JSON 파싱 시도
            import json
            import re
            
            text = response.text
            # JSON 코드 블록 추출
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 코드 블록 없이 JSON만 있는 경우
                json_str = text
            
            result = json.loads(json_str)
            logger.info(f"✅ Trend analysis completed")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini response as JSON: {e}")
            logger.debug(f"Response text: {response.text}")
            return {
                "summary": "분석 실패",
                "main_topics": [],
                "target_audience": [],
                "content_suggestions": [],
                "viral_potential": 0,
                "recommended_platforms": [],
                "keywords": []
            }
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            return {}
    
    async def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10
    ) -> List[str]:
        """
        텍스트에서 키워드 추출
        
        Args:
            text: 분석할 텍스트
            max_keywords: 최대 키워드 수
        
        Returns:
            키워드 리스트
        """
        if not hasattr(self, 'model'):
            logger.error("Gemini API not initialized")
            return []
        
        try:
            prompt = f"""
다음 텍스트에서 가장 중요한 키워드 {max_keywords}개를 추출해주세요.
각 키워드는 한 줄에 하나씩, 번호나 기호 없이 작성해주세요.

텍스트:
{text}

키워드:
"""
            
            response = self.model.generate_content(prompt)
            keywords = [k.strip() for k in response.text.strip().split('\n') if k.strip()]
            
            logger.info(f"✅ Extracted {len(keywords)} keywords")
            return keywords[:max_keywords]
            
        except Exception as e:
            logger.error(f"❌ Failed to extract keywords: {e}")
            return []
