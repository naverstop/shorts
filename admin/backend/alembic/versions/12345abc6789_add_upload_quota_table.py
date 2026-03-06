"""add upload quota table

Revision ID: 12345abc6789
Revises: 88327b5de01e
Create Date: 2026-03-02 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12345abc6789'
down_revision: Union[str, None] = '88327b5de01e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create upload_quotas table"""
    op.create_table(
        'upload_quotas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        
        # Limits
        sa.Column('daily_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('weekly_limit', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('monthly_limit', sa.Integer(), nullable=False, server_default='0'),
        
        # Usage
        sa.Column('used_today', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used_week', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('used_month', sa.Integer(), nullable=False, server_default='0'),
        
        # Reset timestamps
        sa.Column('last_daily_reset', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_weekly_reset', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_monthly_reset', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'platform_id', name='uq_user_platform_quota'),
    )
    
    # Create indexes
    op.create_index('ix_upload_quotas_user_id', 'upload_quotas', ['user_id'])
    op.create_index('ix_upload_quotas_platform_id', 'upload_quotas', ['platform_id'])


def downgrade() -> None:
    """Drop upload_quotas table"""
    op.drop_index('ix_upload_quotas_platform_id', table_name='upload_quotas')
    op.drop_index('ix_upload_quotas_user_id', table_name='upload_quotas')
    op.drop_table('upload_quotas')
