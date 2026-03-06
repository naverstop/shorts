"""
Platform Account Models
플랫폼별 계정 관리 모델 (user_platform_credentials 대체)
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class PlatformAccount(Base):
    """
    플랫폼 계정 정보 (SIM별로 여러 플랫폼 계정 가능)
    - SimCard와 N:1 관계
    - Platform과 N:1 관계
    - UploadQuota와 1:1 관계
    """
    __tablename__ = "platform_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    sim_id = Column(Integer, ForeignKey("sim_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 계정 정보
    account_name = Column(String(100))  # "게임채널 A", "음악채널 B"
    account_identifier = Column(String(100))  # 채널 ID, 사용자명 등
    
    # 인증 정보 (암호화됨)
    credentials = Column(JSONB, nullable=False)  # OAuth tokens, cookies 등
    
    # 상태 정보
    status = Column(String(20), default="active", nullable=False, index=True)  # active, expired, banned, invalid
    last_validated = Column(DateTime(timezone=True))  # 마지막 검증 시각
    last_used = Column(DateTime(timezone=True))  # 마지막 사용 시각
    ban_detected_at = Column(DateTime(timezone=True))  # Ban 감지 시각
    ban_reason = Column(Text())  # Ban 사유
    
    # 메타데이터
    is_primary = Column(Boolean, default=False)  # SIM 내에서 주 계정 여부
    notes = Column(Text())
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="platform_accounts")
    sim_card = relationship("SimCard", back_populates="platform_accounts")
    platform = relationship("Platform")
    upload_quota = relationship("UploadQuota", back_populates="platform_account", uselist=False, cascade="all, delete-orphan")
    stats = relationship("PlatformAccountStats", back_populates="platform_account", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PlatformAccount(id={self.id}, sim_id={self.sim_id}, platform_id={self.platform_id}, account_name='{self.account_name}', status='{self.status}')>"
    
    @property
    def display_name(self) -> str:
        """표시용 이름"""
        if self.account_name:
            return self.account_name
        return f"{self.platform.platform_name} Account #{self.id}"
    
    @property
    def is_active(self) -> bool:
        """활성 상태 여부"""
        return self.status == "active"
    
    @property
    def is_banned(self) -> bool:
        """Ban 상태 여부"""
        return self.status == "banned"
    
    @property
    def is_expired(self) -> bool:
        """만료 상태 여부"""
        return self.status == "expired"
    
    @property
    def has_quota(self) -> bool:
        """할당량 설정 여부"""
        return self.upload_quota is not None
    
    @property
    def quota_status(self) -> dict:
        """할당량 상태 요약"""
        if not self.has_quota:
            return {"set": False}
        
        quota = self.upload_quota
        return {
            "set": True,
            "daily": {"used": quota.used_today, "limit": quota.daily_limit, "remaining": quota.get_remaining_daily()},
            "weekly": {"used": quota.used_week, "limit": quota.weekly_limit, "remaining": quota.get_remaining_weekly()},
            "monthly": {"used": quota.used_month, "limit": quota.monthly_limit, "remaining": quota.get_remaining_monthly()},
            "exceeded": quota.is_quota_exceeded()
        }
    
    def can_upload(self) -> bool:
        """업로드 가능 여부"""
        if not self.is_active:
            return False
        if not self.has_quota:
            return True  # 할당량 미설정 시 제한 없음
        return not self.upload_quota.is_quota_exceeded()
    
    def mark_as_banned(self, reason: str = None):
        """Ban 상태로 변경"""
        self.status = "banned"
        self.ban_detected_at = func.now()
        if reason:
            self.ban_reason = reason
    
    def mark_as_expired(self):
        """만료 상태로 변경"""
        self.status = "expired"
    
    def mark_as_active(self):
        """활성 상태로 복구"""
        self.status = "active"
        self.ban_detected_at = None
        self.ban_reason = None


class PlatformAccountStats(Base):
    """
    플랫폼 계정 통계 (모니터링용)
    """
    __tablename__ = "platform_account_stats"

    id = Column(Integer, primary_key=True, index=True)
    platform_account_id = Column(Integer, ForeignKey("platform_accounts.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    
    # 업로드 통계
    total_uploads = Column(Integer, default=0, nullable=False)
    successful_uploads = Column(Integer, default=0, nullable=False)
    failed_uploads = Column(Integer, default=0, nullable=False)
    
    # 마지막 활동
    last_upload_at = Column(DateTime(timezone=True))
    last_successful_upload_at = Column(DateTime(timezone=True))
    last_failed_upload_at = Column(DateTime(timezone=True))
    
    # 에러 추적
    consecutive_failures = Column(Integer, default=0, nullable=False)
    last_error_message = Column(Text())
    
    # 상태 변경 이력
    status_changes = Column(JSONB)  # [{"timestamp": "...", "old_status": "...", "new_status": "...", "reason": "..."}]
    
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    platform_account = relationship("PlatformAccount", back_populates="stats")

    def __repr__(self):
        return f"<PlatformAccountStats(account_id={self.platform_account_id}, total={self.total_uploads}, success={self.successful_uploads}, fail={self.failed_uploads})>"
    
    @property
    def success_rate(self) -> float:
        """성공률 (%)"""
        if self.total_uploads == 0:
            return 0.0
        return (self.successful_uploads / self.total_uploads) * 100
    
    def record_upload_success(self):
        """업로드 성공 기록"""
        self.total_uploads += 1
        self.successful_uploads += 1
        self.last_upload_at = func.now()
        self.last_successful_upload_at = func.now()
        self.consecutive_failures = 0  # 리셋
    
    def record_upload_failure(self, error_message: str = None):
        """업로드 실패 기록"""
        self.total_uploads += 1
        self.failed_uploads += 1
        self.last_upload_at = func.now()
        self.last_failed_upload_at = func.now()
        self.consecutive_failures += 1
        if error_message:
            self.last_error_message = error_message
    
    def record_status_change(self, old_status: str, new_status: str, reason: str = None):
        """상태 변경 이력 기록"""
        if self.status_changes is None:
            self.status_changes = []
        
        change_record = {
            "timestamp": func.now().isoformat(),
            "old_status": old_status,
            "new_status": new_status,
        }
        if reason:
            change_record["reason"] = reason
        
        self.status_changes.append(change_record)
