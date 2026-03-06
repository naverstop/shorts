"""
Authentication API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, Token
from app.auth import verify_password, get_password_hash, create_access_token
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/test")
async def test_auth():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Auth router is working"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        print(f"🔍 Register request received: {user_data.username}")
        
        # Check if username already exists
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email already exists
        result = await db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        print(f"🔐 Hashing password for user: {user_data.username}")
        hashed_password = get_password_hash(user_data.password)
        print(f"✅ Password hashed successfully")
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=1,
            is_admin=0,
            role="user"
        )
        
        db.add(new_user)
        await db.flush()  # flush instead of commit
        await db.refresh(new_user)
        
        print(f"✅ User created: ID={new_user.id}")
        
        # Return simple dict instead of model
        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role,
            "created_at": str(new_user.created_at) if new_user.created_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Login and get access token"""
    # Find user by username
    result = await db.execute(
        select(User).where(User.username == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.post("/logout")
async def logout():
    """Logout (client should remove token)"""
    return {"message": "Successfully logged out"}
