"""
YouTube Publish Service
완료된 Job의 렌더링 결과 영상을 YouTube에 게시
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.platform import Platform, UserPlatformCredential
from app.utils.crypto import decrypt_dict_from_db, encrypt_dict_for_db


class YouTubePublishService:
    async def publish_job(
        self,
        db: AsyncSession,
        user_id: int,
        job_id: int,
        credential_id: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None,
        privacy_status: str = "private",
    ) -> dict:
        job_result = await db.execute(
            select(Job).where(and_(Job.id == job_id, Job.user_id == user_id))
        )
        job = job_result.scalar_one_or_none()
        if not job:
            raise ValueError("Job not found")

        metadata = dict(job.job_metadata or {})
        video_path = metadata.get("video_path")
        if not video_path or not os.path.exists(video_path):
            raise ValueError("Uploaded video file not found for this job")

        credential = await self._resolve_credential(
            db=db,
            user_id=user_id,
            credential_id=credential_id,
        )

        decrypted = decrypt_dict_from_db(dict(credential.credentials or {}))
        credentials = Credentials(
            token=decrypted.get("access_token"),
            refresh_token=decrypted.get("refresh_token"),
            token_uri=decrypted.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=decrypted.get("client_id"),
            client_secret=decrypted.get("client_secret"),
            scopes=decrypted.get("scopes"),
        )

        if (not credentials.valid) and credentials.refresh_token:
            credentials.refresh(Request())
            decrypted["access_token"] = credentials.token
            decrypted["refresh_token"] = credentials.refresh_token or decrypted.get("refresh_token")
            decrypted["expiry"] = credentials.expiry.isoformat() if credentials.expiry else None
            credential.credentials = encrypt_dict_for_db(decrypted)
            credential.last_validated = datetime.utcnow()

        publish_title = (title or job.title or f"Job #{job.id}").strip()[:100]
        publish_description = (description or job.script or "").strip()[:5000]
        publish_tags = tags or ["shorts", "ai", "auto"]

        upload_result = await asyncio.to_thread(
            self._upload_video,
            video_path,
            publish_title,
            publish_description,
            publish_tags,
            privacy_status,
            credentials,
        )

        video_id = upload_result.get("id")
        video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

        metadata["youtube_upload"] = {
            "video_id": video_id,
            "video_url": video_url,
            "published_at": datetime.now(timezone.utc).isoformat(),
            "credential_id": credential.id,
            "privacy_status": privacy_status,
            "title": publish_title,
        }
        job.job_metadata = metadata

        return {
            "status": "published",
            "platform": "youtube",
            "job_id": job.id,
            "video_id": video_id,
            "video_url": video_url,
            "credential_id": credential.id,
        }

    async def _resolve_credential(
        self,
        db: AsyncSession,
        user_id: int,
        credential_id: Optional[int],
    ) -> UserPlatformCredential:
        if credential_id is not None:
            result = await db.execute(
                select(UserPlatformCredential)
                .join(Platform, Platform.id == UserPlatformCredential.platform_id)
                .where(
                    and_(
                        UserPlatformCredential.id == credential_id,
                        UserPlatformCredential.user_id == user_id,
                        Platform.platform_code == "youtube",
                    )
                )
            )
            credential = result.scalar_one_or_none()
            if not credential:
                raise ValueError("YouTube credential not found")
            return credential

        result = await db.execute(
            select(UserPlatformCredential)
            .join(Platform, Platform.id == UserPlatformCredential.platform_id)
            .where(
                and_(
                    UserPlatformCredential.user_id == user_id,
                    UserPlatformCredential.status == "active",
                    Platform.platform_code == "youtube",
                )
            )
            .order_by(desc(UserPlatformCredential.is_default), desc(UserPlatformCredential.created_at))
            .limit(1)
        )
        credential = result.scalar_one_or_none()
        if not credential:
            raise ValueError("No active YouTube credential found")
        return credential

    def _upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        privacy_status: str,
        credentials: Credentials,
    ) -> dict:
        youtube = build("youtube", "v3", credentials=credentials)

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "selfDeclaredMadeForKids": False,
                },
            },
            media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=True),
        )

        response = None
        while response is None:
            _, response = request.next_chunk()

        return response
