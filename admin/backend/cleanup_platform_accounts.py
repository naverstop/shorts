"""
플랫폼 계정 정리
"""
import asyncio
from sqlalchemy import delete
from app.database import AsyncSessionLocal
from app.models import PlatformAccount, PlatformAccountStats

async def cleanup():
    print("="*80)
    print("🧹 플랫폼 계정 정리")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        try:
            # 통계 삭제
            result = await db.execute(delete(PlatformAccountStats))
            stats_deleted = result.rowcount
            
            # 계정 삭제
            result = await db.execute(delete(PlatformAccount))
            accounts_deleted = result.rowcount
            
            await db.commit()
            
            print(f"\n✅ 정리 완료!")
            print(f"   - 삭제된 통계: {stats_deleted}개")
            print(f"   - 삭제된 계정: {accounts_deleted}개")
        except Exception as e:
            print(f"\n❌ 오류: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(cleanup())
