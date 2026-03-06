"""
Script Service
- AI 스크립트 생성
- Vector 유사도 검색
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from loguru import logger

from app.models.script import Script
from app.models.trend import Trend
from app.services.claude_client import ClaudeClient
from app.services.embedding_client import EmbeddingClient


class ScriptService:
    """스크립트 생성 및 관리 서비스"""
    
    def __init__(self):
        self.claude_client = ClaudeClient()
        self.embedding_client = EmbeddingClient()

    @staticmethod
    def _calculate_quality_score(script_data: dict) -> float:
        """스크립트 품질 점수(0~100) 계산"""
        title = script_data.get("title", "") or ""
        hook = script_data.get("hook", "") or ""
        body = script_data.get("body", "") or ""
        cta = script_data.get("cta", "") or ""
        full_script = script_data.get("full_script", "") or ""

        length_score = min(len(full_script) / 12.0, 35.0)
        structure_score = 0.0
        if title.strip():
            structure_score += 10.0
        if hook.strip():
            structure_score += 15.0
        if body.strip():
            structure_score += 20.0
        if cta.strip():
            structure_score += 10.0

        readability_bonus = 0.0
        sentence_count = max(full_script.count("."), 1)
        avg_sentence_len = len(full_script) / sentence_count
        if 25 <= avg_sentence_len <= 90:
            readability_bonus = 10.0

        return round(min(length_score + structure_score + readability_bonus, 100.0), 2)

    @staticmethod
    def _calculate_viral_potential(script_data: dict, trend_score: Optional[float] = None) -> float:
        """바이럴 잠재 점수(0~100) 계산"""
        hook = (script_data.get("hook", "") or "").lower()
        cta = (script_data.get("cta", "") or "").lower()
        title = (script_data.get("title", "") or "").lower()

        score = 30.0

        trigger_keywords = ["충격", "비밀", "반전", "why", "how", "secret", "viral"]
        if any(keyword in hook or keyword in title for keyword in trigger_keywords):
            score += 18.0

        if "?" in hook or "?" in title:
            score += 10.0

        if any(word in cta for word in ["댓글", "공유", "subscribe", "follow", "좋아요"]):
            score += 12.0

        if trend_score is not None:
            score += max(min(trend_score, 100.0), 0.0) * 0.3

        return round(min(score, 100.0), 2)
    
    async def generate_script(
        self,
        db: AsyncSession,
        user_id: int,
        topic: str,
        trend_id: Optional[int] = None,
        target_audience: str = "20-30대",
        platform: str = "youtube_shorts",
        language: str = "ko",
        duration: int = 60
    ) -> Optional[Script]:
        """
        새로운 스크립트 생성
        
        Args:
            db: Database session
            user_id: 사용자 ID
            topic: 주제
            trend_id: 관련 트렌드 ID (옵션)
            target_audience: 타겟 청중
            platform: 플랫폼
            language: 언어
            duration: 영상 길이
        
        Returns:
            생성된 Script 객체
        """
        try:
            logger.info(f"📝 Generating script for topic: {topic}")
            
            # Claude로 스크립트 생성
            script_data = await self.claude_client.generate_script(
                topic=topic,
                target_audience=target_audience,
                platform=platform,
                language=language,
                duration=duration
            )
            
            if not script_data:
                logger.error("Script generation failed")
                return None
            
            # Embedding 생성
            full_script = script_data.get("full_script", "")
            embedding = await self.embedding_client.create_embedding(full_script)
            
            if not embedding:
                logger.warning("Failed to create embedding, continuing without it")
            
            # Script 저장
            trend_score = None
            if trend_id is not None:
                trend_result = await db.execute(
                    select(Trend).where(Trend.id == trend_id)
                )
                trend = trend_result.scalar_one_or_none()
                if trend is not None:
                    trend_score = float(trend.trend_score or 0.0)

            quality_score = self._calculate_quality_score(script_data)
            viral_potential = self._calculate_viral_potential(script_data, trend_score=trend_score)

            script    = Script(
                user_id=user_id,
                trend_id=trend_id,
                title=script_data.get("title", topic),
                content=full_script,
                hook=script_data.get("hook", ""),
                body=script_data.get("body", ""),
                cta=script_data.get("cta", ""),
                embedding=embedding,
                ai_model=script_data.get("ai_model", "claude-3.5-sonnet"),
                generation_prompt=f"Topic: {topic}, Audience: {target_audience}, Platform: {platform}",
                generation_params={
                    "duration": duration,
                    "language": language,
                    "platform": platform
                },
                quality_score=quality_score,
                viral_potential=viral_potential,
                language=language,
                target_platforms=[platform],
                target_audience={"description": target_audience}
            )
            
            db.add(script)
            await db.commit()
            await db.refresh(script)
            
            logger.info(f"✅ Script created: ID={script.id}")
            return script
            
        except Exception as e:
            logger.error(f"❌ Failed to generate script: {e}")
            await db.rollback()
            return None
    
    async def find_similar_scripts(
        self,
        db: AsyncSession,
        script_id: int,
        similarity_threshold: float = 0.85,
        limit: int = 10
    ) -> List[Dict]:
        """
        유사한 스크립트 검색 (Vector 유사도)
        
        Args:
            db: Database session
            script_id: 기준 스크립트 ID
            similarity_threshold: 유사도 임계값 (0.0 ~ 1.0)
            limit: 최대 결과 수
        
        Returns:
            유사 스크립트 리스트 (similarity 포함)
        """
        try:
            # 기준 스크립트 조회
            result = await db.execute(
                select(Script).where(Script.id == script_id)
            )
            source_script = result.scalar_one_or_none()
            
            if not source_script or not source_script.embedding:
                logger.warning(f"Script {script_id} not found or has no embedding")
                return []
            
            # pgvector cosine similarity 검색
            # <-> 연산자: cosine distance (1 - cosine_similarity)
            query = text("""
                SELECT 
                    id,
                    title,
                    content,
                    user_id,
                    created_at,
                    1 - (embedding <=> :source_embedding) as similarity
                FROM scripts
                WHERE 
                    id != :source_id
                    AND embedding IS NOT NULL
                    AND (1 - (embedding <=> :source_embedding)) >= :threshold
                ORDER BY embedding <=> :source_embedding
                LIMIT :limit
            """)
            
            result = await db.execute(
                query,
                {
                    "source_embedding": str(source_script.embedding),
                    "source_id": script_id,
                    "threshold": similarity_threshold,
                    "limit": limit
                }
            )
            
            similar_scripts = []
            for row in result:
                similar_scripts.append({
                    "id": row.id,
                    "title": row.title,
                    "content": row.content[:200] + "...",
                    "user_id": row.user_id,
                    "created_at": row.created_at,
                    "similarity": float(row.similarity)
                })
            
            logger.info(f"🔍 Found {len(similar_scripts)} similar scripts (threshold: {similarity_threshold})")
            return similar_scripts
            
        except Exception as e:
            logger.error(f"❌ Failed to find similar scripts: {e}")
            return []
    
    async def get_user_scripts(
        self,
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> List[Script]:
        """
        사용자 스크립트 목록 조회
        
        Args:
            db: Database session
            user_id: 사용자 ID
            skip: 건너뛸 개수
            limit: 최대 결과 수
        
        Returns:
            Script 리스트
        """
        try:
            query = select(Script).where(
                Script.user_id == user_id
            ).order_by(desc(Script.created_at)).offset(skip).limit(limit)
            
            result = await db.execute(query)
            scripts = result.scalars().all()
            
            logger.info(f"📋 Found {len(scripts)} scripts for user {user_id}")
            return list(scripts)
            
        except Exception as e:
            logger.error(f"❌ Failed to get user scripts: {e}")
            return []
