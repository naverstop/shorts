"""
DB SIM 카드 데이터 정리
"""
import asyncio
from sqlalchemy import select, delete
from app.database import AsyncSessionLocal
from app.models import SimCard, PlatformAccount

async def cleanup_sim_data():
    print("="*80)
    print("🧹 SIM 카드 데이터 정리")
    print("="*80)
    
    async with AsyncSessionLocal() as db:
        try:
            # 기존 SIM 카드 조회
            result = await db.execute(select(SimCard))
            sims = result.scalars().all()
            
            print(f"\n📊 기존 SIM 카드: {len(sims)}개")
            for sim in sims:
                print(f"   - ID: {sim.id}, {sim.sim_number} ({sim.carrier}) - User: {sim.user_id}")
            
            if len(sims) > 0:
                # 플랫폼 계정 먼저 삭제 (외래 키 제약)
                result = await db.execute(delete(PlatformAccount))
                deleted_accounts = result.rowcount
                
                # SIM 카드 삭제
                result = await db.execute(delete(SimCard))
                deleted_sims = result.rowcount
                
                await db.commit()
                
                print(f"\n✅ 데이터 정리 완료!")
                print(f"   - 삭제된 플랫폼 계정: {deleted_accounts}개")
                print(f"   - 삭제된 SIM 카드: {deleted_sims}개")
            else:
                print("\n✓ 정리할 데이터가 없습니다.")
                
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(cleanup_sim_data())
