"""
SIM Card API 테스트
"""
import asyncio
import sys
from app.database import AsyncSessionLocal
from app.models import User, SimCard, PlatformAccount, Platform
from sqlalchemy import select


async def test_sim_api():
    """SIM Card API 기능 테스트"""
    print("="*60)
    print("🧪 SIM Card API 테스트 시작")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. 테스트 사용자 확인
            result = await db.execute(select(User).limit(1))
            test_user = result.scalar_one_or_none()
            if not test_user:
                print("❌ 테스트 사용자가 없습니다.")
                return
            print(f"\n1️⃣ 테스트 사용자: {test_user.username} (ID: {test_user.id})")
            
            # 2. 플랫폼 확인
            result = await db.execute(select(Platform))
            platforms = result.scalars().all()
            print(f"\n2️⃣ 사용 가능한 플랫폼: {len(platforms)}개")
            youtube = next((p for p in platforms if p.platform_code == "youtube"), platforms[0] if platforms else None)
            if youtube:
                print(f"   - YouTube ID: {youtube.id}")
            
            # 3. SIM 생성/조회
            print(f"\n3️⃣ SIM 생성/조회 테스트...")
            result = await db.execute(select(SimCard).where(SimCard.sim_number == "010-2222-3333"))
            test_sim = result.scalar_one_or_none()
            
            if test_sim:
                print(f"   ✓ 기존 SIM 사용: ID={test_sim.id}, {test_sim.sim_number}")
            else:
                test_sim = SimCard(
                    user_id=test_user.id,
                    sim_number="010-2222-3333",
                    carrier="KT",
                    google_email="test_api@gmail.com",
                    nickname="API 테스트 SIM",
                    status="active",
                    google_account_status="active"
                )
                db.add(test_sim)
                await db.flush()
                print(f"   ✓ SIM 생성: ID={test_sim.id}, {test_sim.sim_number}")
            
            # 4. SIM 조회
            result = await db.execute(
                select(SimCard).where(SimCard.user_id == test_user.id)
            )
            user_sims = result.scalars().all()
            print(f"\n4️⃣ 사용자 SIM 목록: {len(user_sims)}개")
            for sim in user_sims:
                print(f"   - {sim.sim_number} ({sim.carrier}) - {sim.status}")
            
            # 5. 플랫폼 계정 조회/생성
            if youtube:
                print(f"\n5️⃣ 플랫폼 계정 조회/생성...")
                result = await db.execute(
                    select(PlatformAccount).where(
                        PlatformAccount.sim_id == test_sim.id,
                        PlatformAccount.platform_id == youtube.id
                    )
                )
                existing_accounts = result.scalars().all()
                
                if existing_accounts:
                    test_account = existing_accounts[0]
                    print(f"   ✓ 기존 계정 사용: ID={test_account.id}, {test_account.account_name}")
                else:
                    test_account = PlatformAccount(
                        user_id=test_user.id,
                        sim_id=test_sim.id,
                        platform_id=youtube.id,
                        account_name="API 테스트 YouTube 계정",
                        account_identifier="test_channel_api",
                        credentials={"access_token": "test_api_token"},
                        status="active",
                        is_primary=True
                    )
                    db.add(test_account)
                    await db.flush()
                    print(f"   ✓ 계정 생성: ID={test_account.id}, {test_account.account_name}")
                
                # 6. SIM 재조회 (계정 포함)
                await db.refresh(test_sim)
                from sqlalchemy.orm import selectinload
                result = await db.execute(
                    select(SimCard)
                    .options(selectinload(SimCard.platform_accounts))
                    .where(SimCard.id == test_sim.id)
                )
                sim_with_accounts = result.scalar_one()
                print(f"\n6️⃣ SIM 계정 확인:")
                print(f"   - SIM: {sim_with_accounts.sim_number}")
                print(f"   - 등록된 계정: {len(sim_with_accounts.platform_accounts)}개")
                if sim_with_accounts.platform_accounts:
                    for acc in sim_with_accounts.platform_accounts:
                        print(f"     • {acc.account_name} ({acc.status})")
            
            # 7. 커밋
            await db.commit()
            print(f"\n7️⃣ 데이터 저장 완료!")
            
            # 최종 통계
            result = await db.execute(select(SimCard).where(SimCard.user_id == test_user.id))
            final_sims = result.scalars().all()
            result = await db.execute(select(PlatformAccount).where(PlatformAccount.user_id == test_user.id))
            final_accounts = result.scalars().all()
            
            print("\n" + "="*60)
            print("✅ SIM Card API 테스트 완료!")
            print("="*60)
            print(f"\n📊 최종 통계:")
            print(f"  - 총 SIM: {len(final_sims)}개")
            print(f"  - 총 플랫폼 계정: {len(final_accounts)}개")
            print(f"\n🚀 다음 단계:")
            print(f"  1. Backend 서버 실행: uvicorn app.main:app --reload --port 8001")
            print(f"  2. Frontend 서버 실행: cd admin/frontend && npm run dev")
            print(f"  3. 브라우저에서 http://localhost:3000 접속")
            print(f"  4. SIM 카드 메뉴에서 확인")
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(test_sim_api())
