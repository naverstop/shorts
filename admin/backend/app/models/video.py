"""
Video Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, ARRAY, BigInteger, DECIMAL, func
from sqlalchemy.orm import relationship
from app.database import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False, index=True)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False, index=True)
    platform = Column(String(20), nullable=False, index=True)
    video_url = Column(Text)
    video_id = Column(String(100), index=True)
    title = Column(Text)
    description = Column(Text)
    tags = Column(ARRAY(Text))
    language = Column(String(10), index=True)
    duration = Column(Integer)  # seconds
    file_size = Column(BigInteger)  # bytes
    thumbnail_url = Column(Text)
    status = Column(String(20), default="uploaded")  # uploaded, processing, live, removed
    
    # Analytics
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    watch_time = Column(Integer, default=0)  # seconds
    revenue = Column(DECIMAL(10, 2), default=0.00)  # USD
    cpm = Column(DECIMAL(10, 2), default=0.00)
    ctr = Column(DECIMAL(5, 2), default=0.00)
    avg_view_duration = Column(Integer, default=0)
    roi_score = Column(DECIMAL(5, 2), default=0.00)
    
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_synced_at = Column(DateTime(timezone=True))

    # Relationships
    job = relationship("Job", back_populates="videos")
    agent = relationship("Agent", back_populates="videos")
    channel = relationship("Channel", back_populates="videos")

    def __repr__(self):
        return f"<Video(id={self.id}, platform='{self.platform}', title='{self.title}')>"
