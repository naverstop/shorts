"""
DB 플랫폼 계정 확인
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import PlatformAccount

async def check_accounts():
    print("="*80)
    print("🔍 플랫폼 계정 확인")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(PlatformAccount))
            accounts = result.scalars().all()
            
            print(f"\n📊 등록된 플랫폼 계정: {len(accounts)}개")
            for acc in accounts:
                print(f"   - ID: {acc.id}, {acc.account_name} (SIM ID: {acc.sim_id}, Platform: {acc.platform_id})")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_accounts())
