"""
DB SIM 카드 확인
"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import SimCard

async def check_sims():
    print("="*80)
    print("🔍 SIM 카드 확인")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(SimCard))
            sims = result.scalars().all()
            
            print(f"\n📊 등록된 SIM 카드: {len(sims)}개")
            for sim in sims:
                print(f"   - ID: {sim.id}, {sim.sim_number} ({sim.carrier}) - User: {sim.user_id}")
                if sim.google_email:
                    print(f"     Google: {sim.google_email}")
                if sim.nickname:
                    print(f"     별칭: {sim.nickname}")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_sims())
