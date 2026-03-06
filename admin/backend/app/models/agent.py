"""
Agent Model (Android Device)
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import INET
from app.database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sim_id = Column(Integer, ForeignKey("sim_cards.id", ondelete="SET NULL"), unique=True, index=True)  # 1:1 with SIM
    device_name = Column(String(100), nullable=False)  # USER{id}_AGENT{seq}_{carrier}
    device_id = Column(String(100), unique=True, nullable=False, index=True)
    api_key = Column(String(128), unique=True, nullable=False, index=True)
    status = Column(String(20), default="idle")  # idle, processing, offline, banned
    last_heartbeat = Column(DateTime(timezone=True))
    ip_address = Column(INET)
    sim_carrier = Column(String(50))
    android_version = Column(String(20))
    apk_version = Column(String(20))
    disk_usage_percent = Column(Integer, default=0)
    last_disk_cleanup = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="agents")
    sim_card = relationship("SimCard", back_populates="agent")  # 1:1
    channels = relationship("Channel", back_populates="agent", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="agent")
    videos = relationship("Video", back_populates="agent")

    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.device_name}', status='{self.status}')>"
