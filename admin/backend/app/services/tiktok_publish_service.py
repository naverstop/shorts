"""
TikTok Publish Service
Playwright 기반 업로드 자동화 시도 (쿠키/세션 기반)
"""
from __future__ import annotations

import asyncio
import importlib
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.platform import Platform, UserPlatformCredential
from app.utils.crypto import decrypt_dict_from_db


class TikTokPublishService:
    async def publish_job(
        self,
        db: AsyncSession,
        user_id: int,
        job_id: int,
        credential_id: Optional[int] = None,
        caption: Optional[str] = None,
        headless: bool = True,
    ) -> dict:
        job_result = await db.execute(select(Job).where(and_(Job.id == job_id, Job.user_id == user_id)))
        job = job_result.scalar_one_or_none()
        if not job:
            raise ValueError("Job not found")

        metadata = dict(job.job_metadata or {})
        video_path = metadata.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise ValueError("Uploaded video file not found for this job")

        credential = await self._resolve_credential(db, user_id, credential_id)
        creds = decrypt_dict_from_db(dict(credential.credentials or {}))

        publish_caption = caption or job.title or f"Job #{job.id}"
        result = await self._upload_via_playwright(video_path=video_path, caption=publish_caption, creds=creds, headless=headless)

        metadata["tiktok_upload"] = {
            "video_url": result.get("video_url"),
            "published_at": datetime.now(timezone.utc).isoformat(),
            "credential_id": credential.id,
            "caption": publish_caption,
            "mode": result.get("mode", "playwright"),
        }
        job.job_metadata = metadata

        return {
            "status": "published",
            "platform": "tiktok",
            "job_id": job.id,
            "video_url": result.get("video_url"),
            "credential_id": credential.id,
        }

    async def _resolve_credential(self, db: AsyncSession, user_id: int, credential_id: Optional[int]) -> UserPlatformCredential:
        if credential_id is not None:
            result = await db.execute(
                select(UserPlatformCredential)
                .join(Platform, Platform.id == UserPlatformCredential.platform_id)
                .where(
                    and_(
                        UserPlatformCredential.id == credential_id,
                        UserPlatformCredential.user_id == user_id,
                        Platform.platform_code == "tiktok",
                    )
                )
            )
            credential = result.scalar_one_or_none()
            if not credential:
                raise ValueError("TikTok credential not found")
            return credential

        result = await db.execute(
            select(UserPlatformCredential)
            .join(Platform, Platform.id == UserPlatformCredential.platform_id)
            .where(
                and_(
                    UserPlatformCredential.user_id == user_id,
                    UserPlatformCredential.status == "active",
                    Platform.platform_code == "tiktok",
                )
            )
            .order_by(desc(UserPlatformCredential.is_default), desc(UserPlatformCredential.created_at))
            .limit(1)
        )
        credential = result.scalar_one_or_none()
        if not credential:
            raise ValueError("No active TikTok credential found")
        return credential

    async def _upload_via_playwright(self, video_path: str, caption: str, creds: dict, headless: bool) -> dict:
        try:
            playwright_async_api = importlib.import_module("playwright.async_api")
            async_playwright = getattr(playwright_async_api, "async_playwright")
        except Exception as e:
            raise ValueError(f"Playwright not available: {e}")

        cookies_json = creds.get("cookies_json")
        if not cookies_json:
            raise ValueError("TikTok credential must include cookies_json for browser session")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()
            try:
                await context.add_cookies(cookies_json)
                await page.goto("https://www.tiktok.com/upload", wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(2500)

                file_input = await page.query_selector('input[type="file"]')
                if file_input is None:
                    raise ValueError("TikTok upload input not found")

                await file_input.set_input_files(video_path)
                await page.wait_for_timeout(3000)

                caption_input = await page.query_selector('div[contenteditable="true"]')
                if caption_input is not None:
                    await caption_input.click()
                    await caption_input.fill(caption)

                publish_button = await page.query_selector('button:has-text("Post")')
                if publish_button is None:
                    publish_button = await page.query_selector('button:has-text("게시")')
                if publish_button is None:
                    raise ValueError("TikTok publish button not found")

                await publish_button.click()
                await page.wait_for_timeout(7000)

                current_url = page.url
                return {
                    "video_url": current_url,
                    "mode": "playwright",
                }
            finally:
                await context.close()
                await browser.close()
