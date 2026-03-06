"""
Claude AI Client
- 바이럴 스크립트 생성
- Hook-Body-CTA 구조 작성
"""
from typing import Dict, Optional
from loguru import logger

from app.config import settings

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic not installed. Claude API disabled.")


class ClaudeClient:
    """
    Anthropic Claude AI 클라이언트
    """
    
    def __init__(self, api_key: Optional[str] = None):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("anthropic is required.")
        
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        if not self.api_key:
            logger.warning("ANTHROPIC_API_KEY not found in environment")
            return
        
        self.client = AsyncAnthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
    
    async def generate_script(
        self,
        topic: str,
        target_audience: str = "20-30대",
        platform: str = "youtube_shorts",
        language: str = "ko",
        duration: int = 60
    ) -> Dict:
        """
        바이럴 스크립트 생성
        
        Args:
            topic: 주제/키워드
            target_audience: 타겟 청중
            platform: 플랫폼 (youtube_shorts, tiktok, instagram_reels)
            language: 언어
            duration: 영상 길이 (초)
        
        Returns:
            스크립트 Dict (hook, body, cta, full_script 포함)
        """
        if not hasattr(self, 'client'):
            logger.error("Claude API not initialized")
            return {}
        
        try:
            platform_specs = {
                "youtube_shorts": "YouTube Shorts (세로형, 최대 60초)",
                "tiktok": "TikTok (트렌디, 빠른 전개)",
                "instagram_reels": "Instagram Reels (시각적, 스타일리시)"
            }
            
            prompt = f"""
당신은 바이럴 쇼츠 영상 스크립트 전문가입니다.

다음 조건으로 {duration}초 분량의 스크립트를 작성해주세요:
- 주제: {topic}
- 타겟 청중: {target_audience}
- 플랫폼: {platform_specs.get(platform, platform)}
- 언어: {language}

스크립트는 Hook-Body-CTA 구조로 작성하고, 다음 JSON 형식으로 응답해주세요:

{{
    "title": "매력적인 제목 (10자 이내)",
    "hook": "첫 3초 도입부 - 시청자의 관심을 즉시 끄는 강력한 훅",
    "body": "본문 내용 - 핵심 메시지를 간결하고 명확하게",
    "cta": "행동 유도 - 좋아요, 구독, 댓글 등 명확한 CTA",
    "full_script": "전체 스크립트 (자연스러운 흐름)",
    "estimated_duration": 60,
    "suggested_visuals": ["비주얼 제안1", "비주얼 제안2"],
    "suggested_music": "추천 배경음악 스타일",
    "hashtags": ["#태그1", "#태그2", "#태그3"]
}}

[중요 원칙]
1. 첫 3초가 생명입니다 - Hook이 강력해야 합니다
2. 짧고 간결하게 - 불필요한 말은 제거
3. 시청 유지율을 높이는 전개 구조
4. 자연스러운 한국어 구어체 사용
5. 감정을 자극하는 스토리텔링
"""
            
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            
            # JSON 파싱
            import json
            import re
            
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
            
            result = json.loads(json_str)
            result["ai_model"] = self.model
            
            logger.info(f"✅ Script generated for topic: {topic}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Claude response as JSON: {e}")
            logger.debug(f"Response text: {response_text}")
            return {
                "title": topic,
                "hook": "",
                "body": "",
                "cta": "",
                "full_script": response_text,
                "estimated_duration": duration,
                "suggested_visuals": [],
                "suggested_music": "",
                "hashtags": []
            }
        except Exception as e:
            logger.error(f"❌ Claude API error: {e}")
            return {}
    
    async def improve_script(
        self,
        script: str,
        feedback: str
    ) -> str:
        """
        스크립트 개선
        
        Args:
            script: 원본 스크립트
            feedback: 개선 피드백
        
        Returns:
            개선된 스크립트
        """
        if not hasattr(self, 'client'):
            logger.error("Claude API not initialized")
            return script
        
        try:
            prompt = f"""
다음 스크립트를 피드백을 반영하여 개선해주세요.

원본 스크립트:
{script}

피드백:
{feedback}

개선된 스크립트만 출력해주세요 (추가 설명 없이).
"""
            
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            improved_script = message.content[0].text.strip()
            logger.info("✅ Script improved")
            return improved_script
            
        except Exception as e:
            logger.error(f"❌ Failed to improve script: {e}")
            return script
