"""
테이블 존재 여부 확인 스크립트
"""
import asyncio
from app.database import engine
from sqlalchemy import text


async def check_tables():
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('trends', 'scripts')")
        )
        tables = [row[0] for row in result]
        
        print('\n✅ 테이블 존재 여부:')
        print(f'  trends: {"있음" if "trends" in tables else "없음"}')
        print(f'  scripts: {"있음" if "scripts" in tables else "없음"}')
        
        if 'trends' in tables or 'scripts' in tables:
            print('\n⚠️ AI Integration 테이블이 이미 존재합니다.')
        else:
            print('\n❌ AI Integration 테이블이 없습니다.')


if __name__ == '__main__':
    asyncio.run(check_tables())
