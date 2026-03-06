"""Test login flow"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from app.auth import verify_password

async def test_login():
    async with AsyncSessionLocal() as db:
        try:
            username = "testuser999"
            password = "test1234"
            
            print(f"1. Finding user '{username}'...")
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"   ❌ User not found")
                return
            
            print(f"   ✅ User found (ID: {user.id})")
            print(f"   - Email: {user.email}")
            print(f"   - Role: {user.role}")
            print(f"   - Hash: {user.hashed_password[:30]}...")
            
            print(f"\n2. Verifying password...")
            is_valid = verify_password(password, user.hashed_password)
            
            if is_valid:
                print(f"   ✅ Password is valid!")
            else:
                print(f"   ❌ Password is invalid!")
                
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login())
