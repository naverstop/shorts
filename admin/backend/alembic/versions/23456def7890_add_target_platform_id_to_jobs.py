"""add target_platform_id to jobs

Revision ID: 23456def7890
Revises: 12345abc6789
Create Date: 2026-03-02 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23456def7890'
down_revision: Union[str, None] = '12345abc6789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add target_platform_id to jobs table"""
    # Add column with nullable first (for existing data)
    op.add_column('jobs', sa.Column('target_platform_id', sa.Integer(), nullable=True))
    
    # Set default value for existing rows (platform 1 = YouTube)
    op.execute("UPDATE jobs SET target_platform_id = 1 WHERE target_platform_id IS NULL")
    
    # Make it non-nullable
    op.alter_column('jobs', 'target_platform_id', nullable=False)
    
    # Add foreign key
    op.create_foreign_key(
        'fk_jobs_target_platform_id',
        'jobs',
        'platforms',
        ['target_platform_id'],
        ['id']
    )
    
    # Add index
    op.create_index('ix_jobs_target_platform_id', 'jobs', ['target_platform_id'])


def downgrade() -> None:
    """Remove target_platform_id from jobs table"""
    op.drop_index('ix_jobs_target_platform_id', table_name='jobs')
    op.drop_constraint('fk_jobs_target_platform_id', 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'target_platform_id')
