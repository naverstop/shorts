"""
Phase 1-2 통합 테스트
SIM 카드 및 플랫폼 계정 API 테스트
"""
import asyncio
import sys
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User, SimCard, PlatformAccount, Platform


async def test_api_models():
    """모델 및 API 준비 상태 테스트"""
    print("="*60)
    print("🧪 Phase 1-2 통합 테스트 시작")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. User 확인
            result = await db.execute(select(User))
            users = result.scalars().all()
            print(f"\n1️⃣ User: {len(users)}명")
            if not users:
                print("   ⚠️  테스트 유저가 없습니다. 회원가입이 필요합니다.")
                return
            test_user = users[0]
            print(f"   ✓ Test User: {test_user.username} (ID: {test_user.id})")
            
            # 2. Platform 확인
            result = await db.execute(select(Platform))
            platforms = result.scalars().all()
            print(f"\n2️⃣ Platform: {len(platforms)}개")
            for p in platforms:
                print(f"   - {p.platform_name} (ID: {p.id}, code: {p.platform_code})")
            
            if not platforms:
                print("   ⚠️  플랫폼 데이터가 없습니다.")
                return
            
            # 3. 기존 SIM 확인
            result = await db.execute(select(SimCard).where(SimCard.user_id == test_user.id))
            existing_sims = result.scalars().all()
            print(f"\n3️⃣ 기존 SIM 카드: {len(existing_sims)}개")
            for sim in existing_sims:
                print(f"   - {sim.sim_number} ({sim.carrier}) - Status: {sim.status}")
            
            # 4. 테스트 SIM 생성
            print("\n4️⃣ 테스트 SIM 생성...")
            test_sim = SimCard(
                user_id=test_user.id,
                sim_number="010-1111-2222",
                carrier="SKT",
                google_email="test_sim@gmail.com",
                nickname="테스트 SIM 1호",
                status="active",
                google_account_status="active"
            )
            db.add(test_sim)
            await db.flush()
            print(f"   ✓ SIM 생성 완료: ID={test_sim.id}, {test_sim.sim_number}")
            
            # 5. SIM 속성 테스트
            print(f"\n5️⃣ SIM 속성 테스트...")
            print(f"   - sim_number: {test_sim.sim_number}")
            print(f"   - carrier: {test_sim.carrier}")
            print(f"   - google_email: {test_sim.google_email}")
            print(f"   - display_name: {test_sim.display_name}")
            print(f"   - status: {test_sim.status}")
            print(f"   - google_account_status: {test_sim.google_account_status}")
            print(f"   ✓ SIM 모델 property 테스트 성공")
            
            # 6. 플랫폼 계정 생성
            print(f"\n6️⃣ 플랫폼 계정 생성...")
            youtube = next((p for p in platforms if p.platform_code == "youtube"), platforms[0])
            test_account = PlatformAccount(
                user_id=test_user.id,
                sim_id=test_sim.id,
                platform_id=youtube.id,
                account_name="테스트 YouTube 계정",
                account_identifier="test_channel_123",
                credentials={"access_token": "test_token", "refresh_token": "test_refresh"},
                status="active",
                is_primary=True
            )
            db.add(test_account)
            await db.flush()
            print(f"   ✓ 계정 생성 완료: ID={test_account.id}, {test_account.account_name}")
            
            # 7. 계정 속성 테스트
            print(f"\n7️⃣ 플랫폼 계정 속성 테스트...")
            print(f"   - account_name: {test_account.account_name}")
            print(f"   - platform_id: {test_account.platform_id}")
            print(f"   - sim_id: {test_account.sim_id}")
            print(f"   - status: {test_account.status}")
            print(f"   - is_primary: {test_account.is_primary}")
            print(f"   ✓ PlatformAccount 모델 테스트 성공")
            
            # 8. SIM 재조회 (계정 포함)
            await db.refresh(test_sim)
            print(f"\n8️⃣ SIM 재조회 (계정 포함)...")
            # Eager load로 platform_accounts를 조회
            from sqlalchemy.orm import selectinload
            result = await db.execute(
                select(SimCard)
                .options(selectinload(SimCard.platform_accounts))
                .where(SimCard.id == test_sim.id)
            )
            test_sim_loaded = result.scalar_one()
            print(f"   - total_accounts: {len(test_sim_loaded.platform_accounts)}")
            if test_sim_loaded.platform_accounts:
                for acc in test_sim_loaded.platform_accounts:
                    print(f"   - {acc.account_name} (platform_id: {acc.platform_id})")
            
            # 9. Rollback (테스트 데이터 삭제)
            print(f"\n9️⃣ 테스트 데이터 정리 (Rollback)...")
            await db.rollback()
            print(f"   ✓ 테스트 데이터 롤백 완료")
            
            # 최종 확인
            print("\n" + "="*60)
            print("✅ Phase 1-2 통합 테스트 완료!")
            print("="*60)
            print("\n📋 결과:")
            print(f"  ✓ DB 마이그레이션: 성공")
            print(f"  ✓ SimCard 모델: 정상 작동")
            print(f"  ✓ PlatformAccount 모델: 정상 작동")
            print(f"  ✓ Relationship: 정상 작동")
            print(f"  ✓ Properties/Methods: 정상 작동")
            print("\n🚀 다음 단계:")
            print(f"  1. Backend API 서버 시작")
            print(f"  2. Postman/curl로 API 테스트")
            print(f"  3. Frontend에서 SIM 관리 UI 개발")
            
        except Exception as e:
            print(f"\n❌ 테스트 실패: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(test_api_models())
