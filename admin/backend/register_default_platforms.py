"""
기본 플랫폼 데이터 등록 스크립트

YouTube, TikTok, Instagram 등 기본 플랫폼을 DB에 등록합니다.
"""
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Platform


async def register_default_platforms():
    """기본 플랫폼 등록"""
    
    default_platforms = [
        {
            "platform_code": "youtube",
            "platform_name": "YouTube",
            "is_active": True,
            "auth_type": "oauth2",
            "api_endpoint": "https://www.googleapis.com/youtube/v3",
            "documentation_url": "https://developers.google.com/youtube/v3",
            "required_fields": {
                "client_id": "Google Cloud Console에서 발급받은 OAuth2 클라이언트 ID",
                "client_secret": "Google Cloud Console에서 발급받은 OAuth2 클라이언트 시크릿",
                "redirect_uri": "OAuth2 리다이렉트 URI",
            }
        },
        {
            "platform_code": "tiktok",
            "platform_name": "TikTok",
            "is_active": True,
            "auth_type": "oauth2",
            "api_endpoint": "https://open-api.tiktok.com",
            "documentation_url": "https://developers.tiktok.com/doc/overview",
            "required_fields": {
                "app_id": "TikTok 개발자 센터에서 발급받은 App ID",
                "app_secret": "TikTok 개발자 센터에서 발급받은 App Secret",
                "redirect_uri": "OAuth2 리다이렉트 URI",
            }
        },
        {
            "platform_code": "instagram",
            "platform_name": "Instagram",
            "is_active": False,  # 아직 미구현
            "auth_type": "oauth2",
            "api_endpoint": "https://graph.instagram.com",
            "documentation_url": "https://developers.facebook.com/docs/instagram-api",
            "required_fields": {
                "app_id": "Facebook 개발자 센터에서 발급받은 App ID",
                "app_secret": "Facebook 개발자 센터에서 발급받은 App Secret",
                "redirect_uri": "OAuth2 리다이렉트 URI",
            }
        },
        {
            "platform_code": "facebook",
            "platform_name": "Facebook Reels",
            "is_active": False,  # 아직 미구현
            "auth_type": "oauth2",
            "api_endpoint": "https://graph.facebook.com",
            "documentation_url": "https://developers.facebook.com/docs/graph-api",
            "required_fields": {
                "app_id": "Facebook 개발자 센터에서 발급받은 App ID",
                "app_secret": "Facebook 개발자 센터에서 발급받은 App Secret",
                "redirect_uri": "OAuth2 리다이렉트 URI",
            }
        },
    ]
    
    async with AsyncSessionLocal() as session:
        session: AsyncSession
        
        created_count = 0
        skipped_count = 0
        
        for platform_data in default_platforms:
            # 중복 확인
            result = await session.execute(
                select(Platform).where(Platform.platform_code == platform_data["platform_code"])
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"⏭️  플랫폼 '{platform_data['platform_name']}' (코드: {platform_data['platform_code']})는 이미 존재합니다.")
                skipped_count += 1
                continue
            
            # 생성
            new_platform = Platform(
                platform_code=platform_data["platform_code"],
                platform_name=platform_data["platform_name"],
                is_active=platform_data["is_active"],
                auth_type=platform_data["auth_type"],
                api_endpoint=platform_data["api_endpoint"],
                documentation_url=platform_data["documentation_url"],
                required_fields=platform_data["required_fields"],
            )
            
            session.add(new_platform)
            print(f"✅ 플랫폼 '{platform_data['platform_name']}' (코드: {platform_data['platform_code']}) 생성 완료")
            created_count += 1
        
        await session.commit()
        
        print("\n" + "="*60)
        print(f"📊 총 {len(default_platforms)}개 플랫폼 처리")
        print(f"   - 생성: {created_count}개")
        print(f"   - 스킵: {skipped_count}개")
        print("="*60)


if __name__ == "__main__":
    print("🚀 기본 플랫폼 데이터 등록 시작...\n")
    asyncio.run(register_default_platforms())
    print("\n✨ 완료!")
