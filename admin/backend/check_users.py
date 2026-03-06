import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User

async def check_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        if not users:
            print("❌ 등록된 사용자가 없습니다.")
            print("\n시나리오 1의 회원가입 단계부터 시작하세요:")
            print("  사용자명: test_creator1")
            print("  이메일: creator1@test.com")
            print("  비밀번호: TestPass123!")
        else:
            print(f"✅ 총 {len(users)}명의 사용자가 등록되어 있습니다:\n")
            for user in users:
                print(f"  - 사용자명: {user.username}")
                print(f"    이메일: {user.email}")
                print(f"    가입일: {user.created_at}")
                print()

if __name__ == "__main__":
    asyncio.run(check_users())
