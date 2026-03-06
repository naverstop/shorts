"""
Gemini AI Client
- 트렌드 분석
- 콘텐츠 구조 분석
"""
import json
import re
from collections import Counter

from typing import Dict, List, Optional
from loguru import logger

from app.config import settings

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
        
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment")
            return
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def _build_fallback_analysis(self, videos: List[Dict], reason: str = "AI 분석 불가") -> Dict:
        """Gemini 사용 불가 시 YouTube 메타데이터 기반 폴백 분석"""
        stopwords = {
            "the", "and", "for", "with", "from", "that", "this", "you", "your",
            "are", "was", "have", "has", "into", "out", "feat", "official",
            "video", "music", "mv", "shorts", "쇼츠", "영상", "공식"
        }

        words: list[str] = []
        for video in videos[:20]:
            title = str(video.get("title", ""))
            tags = video.get("tags", []) or []
            tokens = re.findall(r"[A-Za-z0-9가-힣]{2,}", title)
            tokens.extend(str(tag) for tag in tags[:5])
            for token in tokens:
                normalized = token.strip().lower()
                if len(normalized) >= 2 and normalized not in stopwords:
                    words.append(normalized)

        keyword_counts = Counter(words)
        keywords = [word for word, _ in keyword_counts.most_common(10)]
        main_topics = keywords[:3]
        avg_views = int(sum(v.get("view_count", 0) for v in videos[:10]) / max(len(videos[:10]), 1))
        viral_potential = min(95, max(55, int(avg_views / 100000))) if videos else 55

        return {
            "summary": f"{reason}로 기본 분석 결과를 생성했습니다.",
            "main_topics": main_topics,
            "target_audience": ["YouTube 시청자", "쇼츠 소비층"],
            "content_suggestions": [
                f"{topic} 관련 쇼츠 제작" for topic in main_topics[:3]
            ] or ["현재 인기 주제 기반 쇼츠 제작"],
            "viral_potential": viral_potential,
            "recommended_platforms": ["youtube", "tiktok"],
            "keywords": keywords or ["trending", "youtube", "shorts"],
        }
    
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
            return self._build_fallback_analysis(videos, reason="Gemini JSON 파싱 실패")
        except Exception as e:
            logger.error(f"❌ Gemini API error: {e}")
            return self._build_fallback_analysis(videos, reason="Gemini API 사용 불가")
    
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
