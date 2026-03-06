"""
Script Model - AI 생성 스크립트 with Vector Embedding
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, func, Index, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from app.database import Base


class Script(Base):
    """
    AI 생성 스크립트
    - Claude/Gemini로 생성된 비디오 스크립트
    - Vector Embedding으로 유사도 검색 지원
    """
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trend_id = Column(Integer, ForeignKey("trends.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # 스크립트 내용
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # 스크립트 본문
    hook = Column(Text)  # 도입부 (첫 3초 Hook)
    body = Column(Text)  # 본문
    cta = Column(Text)  # 행동 유도 (Call to Action)
    
    # Vector Embedding (OpenAI text-embedding-3-small: 1536 dimensions)
    embedding = Column(Vector(1536))  # pgvector 타입
    
    # AI 생성 메타데이터
    ai_model = Column(String(50))  # claude-3.5-sonnet, gemini-2.0-flash
    generation_prompt = Column(Text)  # 생성 시 사용한 프롬프트
    generation_params = Column(JSONB)  # AI 생성 파라미터
    
    # 품질 지표
    quality_score = Column(Float, default=0.0)  # AI 품질 점수 (0-100)
    viral_potential = Column(Float, default=0.0)  # 바이럴 가능성 (0-100)
    readability_score = Column(Float)  # 가독성 점수
    
    # 사용 현황
    used_count = Column(Integer, default=0)  # 사용된 횟수
    is_approved = Column(Boolean, default=False)  # 승인 여부
    is_archived = Column(Boolean, default=False, index=True)  # 보관 여부
    
    # 언어 및 타겟
    language = Column(String(10), default="ko", index=True)
    target_platforms = Column(JSONB)  # 타겟 플랫폼 (["youtube", "tiktok"])
    target_audience = Column(JSONB)  # 타겟 청중
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="scripts")
    trend = relationship("Trend")

    # 인덱스
    __table_args__ = (
        Index('idx_script_embedding', 'embedding', postgresql_using='ivfflat'),  # Vector 인덱스
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_quality_viral', 'quality_score', 'viral_potential'),
    )

    def __repr__(self):
        return f"<Script(id={self.id}, title='{self.title[:30]}...', quality={self.quality_score})>"
