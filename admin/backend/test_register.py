"""Test user registration directly"""
import asyncio
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import User
from app.auth import get_password_hash

async def test_register():
    async with AsyncSessionLocal() as db:
        try:
            username = "testuser999"
            email = "testuser999@test.com"
            password = "test1234"
            
            print(f"1. Testing password hash for '{password}'...")
            hashed_password = get_password_hash(password)
            print(f"   ✅ Hash: {hashed_password[:50]}...")
            
            print(f"\n2. Checking if username exists...")
            result = await db.execute(select(User).where(User.username == username))
            existing = result.scalar_one_or_none()
            if existing:
                print(f"   ⚠️  User already exists (ID: {existing.id})")
                return
            
            print(f"\n3. Creating new user...")
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=1,
                is_admin=0,
                role="user"
            )
            
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            print(f"   ✅ User created successfully!")
            print(f"   - ID: {new_user.id}")
            print(f"   - Username: {new_user.username}")
            print(f"   - Email: {new_user.email}")
            print(f"   - Role: {new_user.role}")
            
        except Exception as e:
            print(f"\n❌ Error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_register())
