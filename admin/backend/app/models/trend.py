"""
Trend Model - 트렌드 분석 데이터
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, func, Index
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from app.database import Base


class Trend(Base):
    """
    트렌드 분석 데이터
    - YouTube/TikTok에서 수집한 인기 키워드 및 토픽
    - Gemini를 통한 트렌드 분석 결과
    """
    __tablename__ = "trends"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)  # youtube, tiktok, instagram
    keyword = Column(String(255), nullable=False, index=True)
    topic = Column(String(255))  # 주제 분류
    category = Column(String(100), index=True)  # 카테고리 (예: 뷰티, 게임, 음식)
    
    # 트렌드 메트릭
    trend_score = Column(Float, default=0.0)  # 트렌드 점수 (0-100)
    view_count = Column(Integer, default=0)
    video_count = Column(Integer, default=0)  # 해당 키워드 영상 수
    growth_rate = Column(Float, default=0.0)  # 성장률 (%)
    
    # AI 분석 결과
    ai_analysis = Column(JSONB)  # Gemini 분석 결과 (JSON)
    # {
    #   "summary": "트렌드 요약",
    #   "target_audience": ["20대 여성", "게임 유저"],
    #   "content_suggestions": ["...", "..."],
    #   "viral_potential": 85,
    #   "recommended_platforms": ["youtube", "tiktok"]
    # }
    
    suggested_tags = Column(ARRAY(String))  # 추천 해시태그
    related_keywords = Column(ARRAY(String))  # 연관 키워드
    
    # 메타데이터
    language = Column(String(10), default="ko")  # 언어 코드
    region = Column(String(10), default="KR")  # 지역 코드
    collected_at = Column(DateTime(timezone=True), nullable=False)  # 수집 시간
    expires_at = Column(DateTime(timezone=True))  # 트렌드 만료 예상 시간
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 인덱스
    __table_args__ = (
        Index('idx_trend_score_created', 'trend_score', 'created_at'),
        Index('idx_source_category', 'source', 'category'),
        Index('idx_keyword_source', 'keyword', 'source'),
    )

    def __repr__(self):
        return f"<Trend(id={self.id}, keyword='{self.keyword}', source='{self.source}', score={self.trend_score})>"
