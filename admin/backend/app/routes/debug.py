"""
Simple test endpoint to debug registration
"""
from fastapi import APIRouter
from app.auth import get_password_hash

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])

@router.get("/test-bcrypt")
async def test_bcrypt():
    """Test bcrypt hashing"""
    try:
        password = "test1234"
        hash_result = get_password_hash(password)
        return {
            "status": "success",
            "password_length": len(password),
            "hash_length": len(hash_result),
            "hash_preview": hash_result[:30]
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": type(e).__name__,
            "error_message": str(e)
        }
