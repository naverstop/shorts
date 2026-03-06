"""
Channel Model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship
from app.database import Base


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    # DEPRECATED: v1.0 credential system - use platform_accounts instead
    user_credential_id = Column(Integer, nullable=True)  # ForeignKey removed for v2.0 compatibility
    platform = Column(String(20), nullable=False, index=True)
    channel_id = Column(String(100), nullable=False)
    channel_name = Column(String(100))
    access_token = Column(Text)
    refresh_token = Column(Text)
    status = Column(String(20), default="active")  # active, banned, suspended
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('agent_id', 'platform', name='uq_agent_platform'),
    )

    # Relationships
    agent = relationship("Agent", back_populates="channels")
    # user_credential = relationship("UserPlatformCredential", back_populates="channels")  # DEPRECATED: v1.0
    videos = relationship("Video", back_populates="channel")

    def __repr__(self):
        return f"<Channel(id={self.id}, platform='{self.platform}', name='{self.channel_name}')>"
