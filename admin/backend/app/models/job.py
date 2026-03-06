"""
Job Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, ARRAY, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), index=True)
    target_sim_id = Column(Integer, ForeignKey("sim_cards.id"), index=True)  # 특정 SIM 지정 (선택적)
    target_platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)
    # pending, assigned, rendering, uploading, completed, failed
    priority = Column(Integer, default=5)  # 1(highest) ~ 10(lowest)
    retry_count = Column(Integer, default=0)
    title = Column(Text)
    script = Column(Text)
    source_language = Column(String(10), default="ko")
    target_languages = Column(ARRAY(String(100)))
    job_metadata = Column(JSONB)  # Renamed from 'metadata' (reserved word)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    assigned_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="jobs")
    agent = relationship("Agent", back_populates="jobs")
    target_sim = relationship("SimCard", foreign_keys=[target_sim_id], back_populates="jobs")
    target_platform = relationship("Platform")
    videos = relationship("Video", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, status='{self.status}', title='{self.title}')>"
