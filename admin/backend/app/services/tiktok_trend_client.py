"""
TikTok Trend Client
Playwright 기반 공개 Discover 페이지 트렌드 키워드 수집
"""
from __future__ import annotations

from typing import List


class TikTokTrendClient:
    async def fetch_discover_keywords(self, region_code: str = "KR", limit: int = 20) -> List[str]:
        try:
            from playwright.async_api import async_playwright
        except Exception:
            return []

        url = f"https://www.tiktok.com/discover?lang=en&region={region_code}"
        keywords: list[str] = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)

                anchors = await page.query_selector_all('a[href*="/tag/"]')
                for anchor in anchors:
                    text = (await anchor.inner_text() or "").strip()
                    if not text:
                        continue
                    normalized = text.replace("#", "").strip()
                    if not normalized:
                        continue
                    if normalized not in keywords:
                        keywords.append(normalized)
                    if len(keywords) >= limit:
                        break
            finally:
                await context.close()
                await browser.close()

        return keywords
