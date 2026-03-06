"""
Supported Language Model
"""
from sqlalchemy import Column, Integer, String, Boolean, ARRAY, Text, DateTime, func
from app.database import Base


class SupportedLanguage(Base):
    __tablename__ = "supported_languages"

    id = Column(Integer, primary_key=True, index=True)
    language_code = Column(String(10), unique=True, nullable=False, index=True)
    language_name = Column(String(50), nullable=False)
    native_name = Column(String(50), nullable=False)
    tts_voice_code = Column(String(20))
    is_active = Column(Boolean, default=True)
    popularity_rank = Column(Integer)
    target_markets = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SupportedLanguage(code='{self.language_code}', name='{self.language_name}')>"
