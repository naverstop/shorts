"""
간단한 Upload Quota 테스트 - 직접 함수 호출
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.upload_quota import UploadQuota
from app.routes.upload_quotas import list_upload_quotas
from app.database import DATABASE_URL

# Async engine
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def test_list_quotas():
    """목록 조회 테스트"""
    async with AsyncSessionLocal() as db:
        # Mock user
        from sqlalchemy import select
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ 사용자 없음")
            return
        
        print(f"✅ 사용자 찾음: {user.username} (ID: {user.id})")
        
        # 목록 조회
        try:
            quotas = await list_upload_quotas(
                platform_id=None,
                db=db,
                current_user=user
            )
            print(f"✅ 목록 조회 성공: {len(quotas)}개")
            for q in quotas:
                print(f"   - Quota {q.id}: Platform {q.platform_id}")
        except Exception as e:
            print(f"❌ 목록 조회 실패: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_list_quotas())
