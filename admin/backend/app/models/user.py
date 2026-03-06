"""
User Model
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")  # 'superadmin', 'user'
    is_active = Column(Integer, default=1)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    scripts = relationship("Script", back_populates="user", cascade="all, delete-orphan")
    
    # SIM-centered architecture (v2.0)
    sim_cards = relationship("SimCard", back_populates="user", cascade="all, delete-orphan")
    platform_accounts = relationship("PlatformAccount", back_populates="user", cascade="all, delete-orphan")
    upload_quotas = relationship("UploadQuota", back_populates="user", cascade="all, delete-orphan")
    
    # Legacy (deprecated - will be removed after migration)
    # credentials = relationship("UserPlatformCredential", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def total_sims(self) -> int:
        """등록된 SIM 카드 수"""
        return len(self.sim_cards) if self.sim_cards else 0
    
    @property
    def active_sims(self) -> int:
        """활성 SIM 카드 수"""
        if not self.sim_cards:
            return 0
        return sum(1 for sim in self.sim_cards if sim.status == "active")
    
    @property
    def total_platform_accounts(self) -> int:
        """등록된 플랫폼 계정 수"""
        return len(self.platform_accounts) if self.platform_accounts else 0

