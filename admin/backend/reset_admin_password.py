"""
Admin 비밀번호 초기화 스크립트
"""
import asyncio
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset_admin_password():
    print("="*60)
    print("🔐 Admin 비밀번호 초기화")
    print("="*60)
    
    async with AsyncSessionLocal() as db:
        try:
            # admin 또는 orion0321@gmail.com 사용자 찾기
            result = await db.execute(
                select(User).where(
                    (User.username == "admin") | (User.email == "orion0321@gmail.com")
                )
            )
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                print("❌ admin 사용자를 찾을 수 없습니다.")
                print("   - username='admin' 또는 email='orion0321@gmail.com'")
                return
            
            print(f"\n1️⃣ 사용자 찾음:")
            print(f"   - ID: {admin_user.id}")
            print(f"   - Username: {admin_user.username}")
            print(f"   - Email: {admin_user.email}")
            print(f"   - Role: {admin_user.role}")
            
            # 새 비밀번호 해시 생성
            new_password = "!thdwlstn00"
            hashed_password = pwd_context.hash(new_password)
            
            print(f"\n2️⃣ 새 비밀번호 해시 생성:")
            print(f"   - Password: {new_password}")
            print(f"   - Hash: {hashed_password[:50]}...")
            
            # 비밀번호 업데이트
            admin_user.hashed_password = hashed_password
            await db.commit()
            
            print(f"\n✅ 비밀번호 초기화 완료!")
            print(f"\n📝 로그인 정보:")
            print(f"   - Username: {admin_user.username}")
            print(f"   - Email: {admin_user.email}")
            print(f"   - Password: {new_password}")
            print(f"\n🌐 로그인 URL: http://localhost:3001")
            
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
