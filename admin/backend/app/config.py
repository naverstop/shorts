from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App
    APP_NAME: str = "AI Shorts Generator Admin"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://shorts_admin:shorts_password_2026@localhost:5433/shorts_db"
    DATABASE_ECHO: bool = True
    
    # Redis
    REDIS_URL: str = "redis://:redis_password_2026@localhost:6379/0"
    REDIS_PASSWORD: str = "redis_password_2026"
    
    # JWT
    JWT_SECRET_KEY: str = "your-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # File Storage
    UPLOAD_DIR: str = "./storage/uploads"
    VIDEO_DIR: str = "./storage/videos"
    TEMP_DIR: str = "./storage/temp"
    
    # Logging
    LOG_LEVEL: str = "DEBUG"
    LOG_FILE: str = "./logs/app.log"
    
    # AI Services
    GOOGLE_APPLICATION_CREDENTIALS: str = "./credentials/google-cloud-key.json"
    GOOGLE_CLOUD_PROJECT_ID: str = "your-project-id"
    YOUTUBE_API_KEY: str = "your-youtube-api-key-here"
    GEMINI_API_KEY: str = "your-gemini-api-key-here"
    ANTHROPIC_API_KEY: str = "your-anthropic-api-key-here"
    OPENAI_API_KEY: str = "your-openai-api-key-here"
    
    # Encryption
    ENCRYPTION_KEY: str = "your-encryption-key-32-bytes-base64"
    
    # YouTube OAuth2
    YOUTUBE_CLIENT_ID: str = "your-youtube-client-id.apps.googleusercontent.com"
    YOUTUBE_CLIENT_SECRET: str = "your-youtube-client-secret"
    OAUTH_REDIRECT_URI: str = "http://localhost:8001/api/v1/oauth/youtube/callback"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
