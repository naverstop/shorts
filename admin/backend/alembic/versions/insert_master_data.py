"""Insert master data for platforms and languages

Revision ID: insert_master_data
Revises: 657997b3debf
Create Date: 2026-02-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision: str = 'insert_master_data'
down_revision: Union[str, None] = '657997b3debf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert master data for platforms and supported languages."""
    
    # Insert Platforms
    op.execute(
        sa.text("""
            INSERT INTO platforms (platform_code, platform_name, auth_type, api_endpoint, is_active, required_fields, documentation_url, created_at, updated_at)
            VALUES 
                ('youtube', 'YouTube', 'oauth2', 'https://www.googleapis.com/youtube/v3', true, '{"client_id": "", "client_secret": ""}', 'https://developers.google.com/youtube/v3', NOW(), NOW()),
                ('tiktok', 'TikTok', 'oauth2', 'https://open-api.tiktok.com', true, '{"client_key": "", "client_secret": ""}', 'https://developers.tiktok.com', NOW(), NOW()),
                ('instagram', 'Instagram', 'oauth2', 'https://graph.instagram.com', true, '{"client_id": "", "client_secret": ""}', 'https://developers.facebook.com/docs/instagram-api', NOW(), NOW()),
                ('facebook', 'Facebook', 'oauth2', 'https://graph.facebook.com', true, '{"app_id": "", "app_secret": ""}', 'https://developers.facebook.com/docs/graph-api', NOW(), NOW()),
                ('twitter', 'Twitter/X', 'oauth2', 'https://api.twitter.com/2', true, '{"api_key": "", "api_secret": ""}', 'https://developer.twitter.com/en/docs', NOW(), NOW()),
                ('snapchat', 'Snapchat', 'oauth2', 'https://adsapi.snapchat.com', false, '{"client_id": "", "client_secret": ""}', 'https://developers.snap.com', NOW(), NOW()),
                ('pinterest', 'Pinterest', 'oauth2', 'https://api.pinterest.com/v5', false, '{"app_id": "", "app_secret": ""}', 'https://developers.pinterest.com', NOW(), NOW()),
                ('linkedin', 'LinkedIn', 'oauth2', 'https://api.linkedin.com/v2', false, '{"client_id": "", "client_secret": ""}', 'https://docs.microsoft.com/en-us/linkedin', NOW(), NOW())
            ON CONFLICT (platform_code) DO NOTHING
        """)
    )
    
    # Insert Supported Languages
    op.execute(
        sa.text("""
            INSERT INTO supported_languages (language_code, language_name, native_name, is_active, popularity_rank, created_at)
            VALUES 
                ('ko', 'Korean', '한국어', true, 1, NOW()),
                ('en', 'English', 'English', true, 2, NOW()),
                ('ja', 'Japanese', '日本語', true, 3, NOW()),
                ('zh', 'Chinese', '中文', true, 4, NOW()),
                ('vi', 'Vietnamese', 'Tiếng Việt', true, 5, NOW()),
                ('es', 'Spanish', 'Español', true, 6, NOW()),
                ('pt', 'Portuguese', 'Português', true, 7, NOW()),
                ('hi', 'Hindi', 'हिन्दी', true, 8, NOW()),
                ('id', 'Indonesian', 'Bahasa Indonesia', true, 9, NOW()),
                ('th', 'Thai', 'ไทย', true, 10, NOW()),
                ('fr', 'French', 'Français', true, 11, NOW()),
                ('ar', 'Arabic', 'العربية', true, 12, NOW()),
                ('de', 'German', 'Deutsch', true, 13, NOW())
            ON CONFLICT (language_code) DO NOTHING
        """)
    )


def downgrade() -> None:
    """Remove master data."""
    op.execute(sa.text("DELETE FROM supported_languages"))
    op.execute(sa.text("DELETE FROM platforms"))
