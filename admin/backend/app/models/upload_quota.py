"""
Upload Quota Models
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class UploadQuota(Base):
    """
    플랫폼 계정별 업로드 제한 관리 (v2.0: PlatformAccount 기준)
    - 일일/주간/월간 업로드 제한 설정
    - 사용량 추적 및 자동 리셋
    """
    __tablename__ = "upload_quotas"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id", ondelete="CASCADE"), nullable=True, unique=True, index=True)  # v2.0: 계정별 할당량
    
    # 제한 설정 (0 = 무제한)
    daily_limit = Column(Integer, default=0, nullable=False)  # 일일 업로드 제한
    weekly_limit = Column(Integer, default=0, nullable=False)  # 주간 업로드 제한
    monthly_limit = Column(Integer, default=0, nullable=False)  # 월간 업로드 제한
    
    # 사용량 추적
    used_today = Column(Integer, default=0, nullable=False)  # 오늘 사용량
    used_week = Column(Integer, default=0, nullable=False)  # 이번 주 사용량
    used_month = Column(Integer, default=0, nullable=False)  # 이번 달 사용량
    
    # 리셋 타임스탬프
    last_daily_reset = Column(DateTime(timezone=True), server_default=func.now())
    last_weekly_reset = Column(DateTime(timezone=True), server_default=func.now())
    last_monthly_reset = Column(DateTime(timezone=True), server_default=func.now())
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('user_id', 'platform_id', name='uq_user_platform_quota'),
    )

    # Relationships
    user = relationship("User", back_populates="upload_quotas")
    platform = relationship("Platform")
    platform_account = relationship("PlatformAccount", back_populates="upload_quota")  # v2.0: 1:1

    def __repr__(self):
        return (
            f"<UploadQuota(id={self.id}, user_id={self.user_id}, platform_id={self.platform_id}, "
            f"daily={self.used_today}/{self.daily_limit}, "
            f"weekly={self.used_week}/{self.weekly_limit}, "
            f"monthly={self.used_month}/{self.monthly_limit})>"
        )
    
    def is_daily_exceeded(self) -> bool:
        """일일 제한 초과 여부"""
        if self.daily_limit == 0:
            return False
        return self.used_today >= self.daily_limit
    
    def is_weekly_exceeded(self) -> bool:
        """주간 제한 초과 여부"""
        if self.weekly_limit == 0:
            return False
        return self.used_week >= self.weekly_limit
    
    def is_monthly_exceeded(self) -> bool:
        """월간 제한 초과 여부"""
        if self.monthly_limit == 0:
            return False
        return self.used_month >= self.monthly_limit
    
    def is_quota_exceeded(self) -> bool:
        """어떤 제한이든 초과 여부"""
        return self.is_daily_exceeded() or self.is_weekly_exceeded() or self.is_monthly_exceeded()
    
    def get_remaining_daily(self) -> int:
        """남은 일일 할당량 (-1 = 무제한)"""
        if self.daily_limit == 0:
            return -1
        return max(0, self.daily_limit - self.used_today)
    
    def get_remaining_weekly(self) -> int:
        """남은 주간 할당량 (-1 = 무제한)"""
        if self.weekly_limit == 0:
            return -1
        return max(0, self.weekly_limit - self.used_week)
    
    def get_remaining_monthly(self) -> int:
        """남은 월간 할당량 (-1 = 무제한)"""
        if self.monthly_limit == 0:
            return -1
        return max(0, self.monthly_limit - self.used_month)
