"""
Direct API endpoint test to see the actual error
"""
import asyncio
import sys
sys.path.insert(0, r"C:\shorts\admin\backend")

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.job import Job
from app.utils.quota_check import check_upload_quota
from app.schemas import JobCreate


async def test_job_creation():
    async with AsyncSessionLocal() as db:
        try:
            # Get user
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.username == "quotauser093543"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ User not found")
                return
            
            print(f"✅ User found: {user.id}")
            
            # Prepare job data
            job_data = JobCreate(
                title="Test Job",
                script="Test script",
                source_language="ko",
                target_languages=["ko"],
                platform_id=1,
                priority=5
            )
            
            print(f"✅ Job data prepared: {job_data}")
            
            # Check quota
            print("\nChecking quota...")
            try:
                await check_upload_quota(
                    user_id=user.id,
                    platform_id=job_data.platform_id,
                    db=db,
                    raise_exception=True
                )
                print("✅ Quota check passed")
            except Exception as e:
                print(f"❌ Quota check failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Create Job
            print("\nCreating Job...")
            try:
                job = Job(
                    user_id=user.id,
                    target_platform_id=job_data.platform_id,
                    title=job_data.title,
                    script=job_data.script,
                    source_language=job_data.source_language,
                    target_languages=job_data.target_languages,
                    job_metadata=job_data.job_metadata,
                    status="pending",
                    priority=job_data.priority
                )
                print(f"✅ Job object created: {job}")
            except Exception as e:
                print(f"❌ Job object creation failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Add to DB
            print("\nAdding to DB...")
            try:
                db.add(job)
                print("✅ Job added to session")
            except Exception as e:
                print(f"❌ Add failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Flush
            print("\nFlushing...")
            try:
                await db.flush()
                print(f"✅ Flush successful, Job ID: {job.id}")
            except Exception as e:
                print(f"❌ Flush failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Refresh
            print("\nRefreshing...")
            try:
                await db.refresh(job)
                print(f"✅ Refresh successful")
            except Exception as e:
                print(f"❌ Refresh failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
            
            # Commit
            print("\nCommitting...")
            try:
                await db.commit()
                print(f"✅ Commit successful")
            except Exception as e:
                print(f"❌ Commit failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
            
            print(f"\n✅✅✅ Job created successfully: ID={job.id}")
            
        except Exception as e:
            print(f"\n❌❌❌ Unexpected error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


if __name__ == "__main__":
    asyncio.run(test_job_creation())
