"""
Platform Models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    platform_code = Column(String(20), unique=True, nullable=False, index=True)
    platform_name = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    auth_type = Column(String(20), nullable=False)  # oauth2, api_key, credentials
    required_fields = Column(JSONB)
    api_endpoint = Column(Text)
    documentation_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    # credentials = relationship("UserPlatformCredential", back_populates="platform")  # DEPRECATED: v1.0

    def __repr__(self):
        return f"<Platform(id={self.id}, code='{self.platform_code}', name='{self.platform_name}')>"


# DEPRECATED: v1.0 Credential System
# Legacy class kept for backward compatibility, but excluded from SQLAlchemy metadata
class UserPlatformCredential:
    """
    DEPRECATED: Use PlatformAccount instead
    This class is kept only for import compatibility with legacy code.
    Do NOT use this in new code.
    """
    pass
