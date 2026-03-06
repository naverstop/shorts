"""
SIM Card Models
SIM 카드 관리 모델 (1:1:N 구조의 핵심)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class SimCard(Base):
    """
    SIM 카드 정보
    - User와 1:N 관계
    - Agent와 1:1 관계
    - PlatformAccount와 1:N 관계
    """
    __tablename__ = "sim_cards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # SIM 정보
    sim_number = Column(String(20), unique=True, nullable=False, index=True)  # 010-1234-5678
    carrier = Column(String(50))  # SKT, KT, LGU+
    
    # Google 계정 (1 SIM = 1 Google Account)
    google_email = Column(String(100), unique=True)
    google_account_status = Column(String(20), default="active", nullable=False)  # active, banned, suspended
    
    # 메타데이터
    nickname = Column(String(100))  # 별칭 (예: "게임채널용 SIM")
    notes = Column(Text())
    status = Column(String(20), default="active", nullable=False, index=True)  # active, inactive, banned
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="sim_cards")
    agent = relationship("Agent", back_populates="sim_card", uselist=False)  # 1:1
    platform_accounts = relationship("PlatformAccount", back_populates="sim_card", cascade="all, delete-orphan")
    jobs = relationship("Job", foreign_keys="Job.target_sim_id", back_populates="target_sim")

    def __repr__(self):
        return f"<SimCard(id={self.id}, sim_number='{self.sim_number}', user_id={self.user_id}, status='{self.status}')>"
    
    @property
    def display_name(self) -> str:
        """표시용 이름 (별칭 또는 SIM 번호)"""
        return self.nickname if self.nickname else self.sim_number
    
    @property
    def agent_status(self) -> str:
        """Agent 연결 상태"""
        if not self.agent:
            return "not_registered"
        return self.agent.status
    
    @property
    def total_accounts(self) -> int:
        """등록된 플랫폼 계정 수"""
        return len(self.platform_accounts) if self.platform_accounts else 0
    
    def get_account_by_platform(self, platform_id: int) -> list:
        """특정 플랫폼의 계정 목록"""
        if not self.platform_accounts:
            return []
        return [acc for acc in self.platform_accounts if acc.platform_id == platform_id]
    
    def is_google_account_active(self) -> bool:
        """Google 계정 활성 상태"""
        return self.google_account_status == "active"
    
    def is_available_for_jobs(self) -> bool:
        """Job 처리 가능 여부"""
        return (
            self.status == "active" and
            self.agent is not None and
            self.agent.status == "online" and
            self.is_google_account_active()
        )
