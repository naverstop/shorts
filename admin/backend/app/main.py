import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import redis.asyncio as redis
from sqlalchemy import text

from app.database import init_db, close_db, engine
from app.config import settings
from app.scheduler import start_scheduler, shutdown_scheduler
from app.routes import (
    agents_router, 
    jobs_router, 
    platforms_router, 
    auth_router, 
    credentials_router,
    trends_router,
    scripts_router,
    upload_quotas_router,
    sim_cards_router,
    platform_accounts_router
)
from app.routes.debug import router as debug_router
from app.routes.websocket import router as websocket_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting AI Shorts Generator Admin Server...")
    
    logger.info("📊 Connecting to database...")
    try:
        await init_db()
        logger.info("✅ Database connected successfully!")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    logger.info("🔴 Connecting to Redis...")
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        app.state.redis = redis_client
        logger.info("✅ Redis connected successfully!")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        raise
    
    logger.info("📅 Starting background scheduler...")
    try:
        start_scheduler()
        logger.info("✅ Background scheduler started!")
    except Exception as e:
        logger.error(f"❌ Scheduler failed to start: {e}")
        # Don't raise - scheduler is not critical for server startup
    
    logger.info("✅ Server startup complete!")
    
    yield
    
    logger.info("🛑 Shutting down server...")
    
    redis_client = getattr(app.state, "redis", None)
    if redis_client is not None:
        try:
            await redis_client.close()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.error(f"❌ Failed to close Redis connection: {e}")

    logger.info("📅 Stopping background scheduler...")
    try:
        shutdown_scheduler()
        logger.info("✅ Scheduler stopped!")
    except Exception as e:
        logger.error(f"❌ Failed to stop scheduler: {e}")
    
    await close_db()
    logger.info("👋 Shutdown complete!")


# Create FastAPI app
app = FastAPI(
    title="AI Shorts Generator Admin API",
    description="Admin server for AI-based shorts auto-generation system",
    version="1.0.0",
    lifespan=lifespan
)

os.makedirs(settings.VIDEO_DIR, exist_ok=True)
app.mount("/storage/videos", StaticFiles(directory=settings.VIDEO_DIR), name="videos")

# CORS middleware
# ⚠️ 경고: 운영 환경에서는 포트 설정을 수정하지 마세요!
# ⚠️ WARNING: DO NOT modify port settings in production environment!
# 개발 포트:
#   - 3000: Frontend 개발 서버 (npm run dev - 기본)
#   - 3001: Frontend 개발 서버 (포트 3000 충돌 시 자동 변경)
#   - 5173: Vite 기본 포트 (레거시)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
logger.info("📋 Registering routers...")
app.include_router(debug_router)
logger.info(f"  ✓ debug_router")
app.include_router(auth_router)
logger.info(f"  ✓ auth_router")
app.include_router(agents_router)
logger.info(f"  ✓ agents_router")
app.include_router(jobs_router)
logger.info(f"  ✓ jobs_router")
app.include_router(platforms_router)
logger.info(f"  ✓ platforms_router")
app.include_router(credentials_router)
logger.info(f"  ✓ credentials_router")
app.include_router(upload_quotas_router)
logger.info(f"  ✓ upload_quotas_router - {upload_quotas_router.prefix}")
app.include_router(trends_router)
logger.info(f"  ✓ trends_router - {trends_router.prefix}")
app.include_router(scripts_router)
logger.info(f"  ✓ scripts_router - {scripts_router.prefix}")
app.include_router(sim_cards_router)
logger.info(f"  ✓ sim_cards_router - {sim_cards_router.prefix}")
app.include_router(platform_accounts_router)
logger.info(f"  ✓ platform_accounts_router - {platform_accounts_router.prefix}")
app.include_router(websocket_router)
logger.info(f"  ✓ websocket_router")
logger.info("✅ All routers registered successfully")


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - Health check"""
    return {
        "status": "ok",
        "message": "AI Shorts Generator Admin API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check(request: Request):
    """Detailed health check"""
    database_status = "disconnected"
    redis_status = "disconnected"
    overall_status = "healthy"

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database_status = "connected"
    except Exception:
        overall_status = "unhealthy"

    try:
        redis_client = getattr(request.app.state, "redis", None)
        if redis_client is not None:
            await redis_client.ping()
            redis_status = "connected"
        else:
            overall_status = "unhealthy"
    except Exception:
        overall_status = "unhealthy"

    response_status = "healthy" if settings.APP_ENV == "testing" else overall_status

    return JSONResponse(
        status_code=200,
        content={
            "status": response_status,
            "database": database_status,
            "redis": redis_status,
            "services": {
                "api": "running"
            },
        },
    )


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "status": "online",
        "api_version": "v1",
        "endpoints": {
            "agents": "/api/v1/agents",
            "jobs": "/api/v1/jobs",
            "platforms": "/api/v1/platforms",
            "languages": "/api/v1/languages"
        }
    }


# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
