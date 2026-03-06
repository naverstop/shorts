"""
UploadQuota API 디버깅용 간단 테스트
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import get_db
from app.models.upload_quota import UploadQuota
from app.models.user import User
from app.models.platform import Platform
import os

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://shorts_user:shorts_password_2026@localhost:5433/shorts_db"
)

print(f"Database URL: {DATABASE_URL}")

# Create engine (sync mode for testing)
engine = create_engine(DATABASE_URL.replace('postgresql+asyncpg:', 'postgresql:'))
SessionLocal = sessionmaker(bind=engine)

try:
    db: Session = SessionLocal()
    
    # 1. User 확인
    print("\n1. Users in database:")
    users = db.query(User).limit(3).all()
    for user in users:
        print(f"   - User {user.id}: {user.username}")
    
    # 2. Platform 확인
    print("\n2. Platforms in database:")
    platforms = db.query(Platform).all()
    for platform in platforms:
        print(f"   - Platform {platform.id}: {platform.platform_name} ({platform.platform_code})")
    
    # 3. Existing quotas
    print("\n3. Existing upload quotas:")
    quotas = db.query(UploadQuota).all()
    if quotas:
        for quota in quotas:
            print(f"   - Quota {quota.id}: User {quota.user_id}, Platform {quota.platform_id}")
    else:
        print("   (No quotas yet)")
    
    # 4. Create test quota
    if users and platforms:
        test_user = users[0]
        test_platform = platforms[0]
        
        print(f"\n4. Creating test quota for User {test_user.id}, Platform {test_platform.id}")
        
        # Check existing
        existing = db.query(UploadQuota).filter(
            UploadQuota.user_id == test_user.id,
            UploadQuota.platform_id == test_platform.id
        ).first()
        
        if existing:
            print(f"   - Quota already exists: {existing.id}")
        else:
            new_quota = UploadQuota(
                user_id=test_user.id,
                platform_id=test_platform.id,
                daily_limit=10,
                weekly_limit=50,
                monthly_limit=200
            )
            db.add(new_quota)
            db.commit()
            db.refresh(new_quota)
            print(f"   - Quota created successfully: {new_quota.id}")
            print(f"   - Daily: {new_quota.used_today}/{new_quota.daily_limit}")
            print(f"   - Remaining daily: {new_quota.get_remaining_daily()}")
            print(f"   - Is exceeded: {new_quota.is_quota_exceeded()}")
    
    db.close()
    print("\n✅ Database operations successful")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
