"""
DB 마이그레이션 테스트 스크립트
"""
import asyncio
from app.database import AsyncSessionLocal
from app.models import SimCard, PlatformAccount, PlatformAccountStats, Agent, Job, UploadQuota


async def check_tables():
    async with AsyncSessionLocal() as session:
        try:
            # 새 테이블 확인
            from sqlalchemy import select
            
            # SimCard
            result = await session.execute(select(SimCard))
            sim_count = len(result.scalars().all())
            print(f"✅ SimCard table: {sim_count} rows")
            
            # PlatformAccount
            result = await session.execute(select(PlatformAccount))
            pa_count = len(result.scalars().all())
            print(f"✅ PlatformAccount table: {pa_count} rows")
            
            # PlatformAccountStats
            result = await session.execute(select(PlatformAccountStats))
            stats_count = len(result.scalars().all())
            print(f"✅ PlatformAccountStats table: {stats_count} rows")
            
            # Agent (sim_id 컬럼 확인)
            result = await session.execute(select(Agent))
            agents = result.scalars().all()
            print(f"✅ Agent table: {len(agents)} rows")
            if agents:
                agent = agents[0]
                has_sim_id = hasattr(agent, 'sim_id')
                print(f"   - sim_id column exists: {has_sim_id}")
            
            # Job (target_sim_id 컬럼 확인)
            result = await session.execute(select(Job))
            jobs = result.scalars().all()
            print(f"✅ Job table: {len(jobs)} rows")
            if jobs:
                job = jobs[0]
                has_target_sim_id = hasattr(job, 'target_sim_id')
                print(f"   - target_sim_id column exists: {has_target_sim_id}")
            
            # UploadQuota (platform_account_id 컬럼 확인)
            result = await session.execute(select(UploadQuota))
            quotas = result.scalars().all()
            print(f"✅ UploadQuota table: {len(quotas)} rows")
            if quotas:
                quota = quotas[0]
                has_platform_account_id = hasattr(quota, 'platform_account_id')
                print(f"   - platform_account_id column exists: {has_platform_account_id}")
            
            print("\n" + "="*60)
            print("✅ Phase 1: DB 마이그레이션 완료!")
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_tables())
