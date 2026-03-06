"""Add SIM cards and redesign architecture

Revision ID: a1b2c3d4e5f6
Revises: 330f7045cc51
Create Date: 2026-03-04 10:00:00.000000

Major changes:
  1. Create sim_cards table (core entity)
  2. Add sim_id to agents (1:1 mapping)
  3. Create platform_accounts (replace user_platform_credentials)
  4. Modify upload_quotas (platform_account_id instead of platform_id)
  5. Modify jobs (add target_sim_id)
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '330f7045cc51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply SIM-centered architecture changes"""
    
    # ==================== 1. Create sim_cards table ====================
    op.create_table(
        'sim_cards',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # SIM 정보
        sa.Column('sim_number', sa.String(length=20), nullable=False),
        sa.Column('carrier', sa.String(length=50), nullable=True),
        
        # Google 계정
        sa.Column('google_email', sa.String(length=100), nullable=True),
        sa.Column('google_account_status', sa.String(length=20), server_default='active', nullable=False),
        
        # 메타데이터
        sa.Column('nickname', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('sim_number', name='uq_sim_number'),
        sa.UniqueConstraint('google_email', name='uq_google_email'),
    )
    
    op.create_index('ix_sim_cards_user_id', 'sim_cards', ['user_id'])
    op.create_index('ix_sim_cards_sim_number', 'sim_cards', ['sim_number'])
    op.create_index('ix_sim_cards_status', 'sim_cards', ['status'])
    
    # ==================== 2. Add sim_id to agents ====================
    op.add_column('agents', sa.Column('sim_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_agents_sim_id', 'agents', 'sim_cards', ['sim_id'], ['id'], ondelete='SET NULL')
    op.create_unique_constraint('uq_agents_sim_id', 'agents', ['sim_id'])
    op.create_index('ix_agents_sim_id', 'agents', ['sim_id'])
    
    # ==================== 3. Create platform_accounts ====================
    op.create_table(
        'platform_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('sim_id', sa.Integer(), nullable=False),
        sa.Column('platform_id', sa.Integer(), nullable=False),
        
        # 계정 정보
        sa.Column('account_name', sa.String(length=100), nullable=True),
        sa.Column('account_identifier', sa.String(length=100), nullable=True),
        
        # 인증 정보 (암호화)
        sa.Column('credentials', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        
        # 상태
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('last_validated', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ban_detected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ban_reason', sa.Text(), nullable=True),
        
        # 메타데이터
        sa.Column('is_primary', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sim_id'], ['sim_cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['platform_id'], ['platforms.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('sim_id', 'platform_id', 'account_name', name='uq_sim_platform_account'),
    )
    
    op.create_index('ix_platform_accounts_user_id', 'platform_accounts', ['user_id'])
    op.create_index('ix_platform_accounts_sim_id', 'platform_accounts', ['sim_id'])
    op.create_index('ix_platform_accounts_platform_id', 'platform_accounts', ['platform_id'])
    op.create_index('ix_platform_accounts_status', 'platform_accounts', ['status'])
    
    # ==================== 4. Modify upload_quotas ====================
    # Add platform_account_id column
    op.add_column('upload_quotas', sa.Column('platform_account_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_upload_quotas_account', 'upload_quotas', 'platform_accounts', ['platform_account_id'], ['id'], ondelete='CASCADE')
    
    # Drop old unique constraint
    op.drop_constraint('uq_user_platform_quota', 'upload_quotas', type_='unique')
    
    # Create new unique constraint
    op.create_unique_constraint('uq_quota_platform_account', 'upload_quotas', ['platform_account_id'])
    op.create_index('ix_upload_quotas_platform_account_id', 'upload_quotas', ['platform_account_id'])
    
    # Drop old platform_id column (after data migration in production)
    # op.drop_column('upload_quotas', 'platform_id')  # 나중에 실행
    
    # ==================== 5. Modify jobs table ====================
    op.add_column('jobs', sa.Column('target_sim_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_jobs_target_sim', 'jobs', 'sim_cards', ['target_sim_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_jobs_target_sim_id', 'jobs', ['target_sim_id'])
    
    # ==================== 6. Create platform_account_stats ====================
    op.create_table(
        'platform_account_stats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform_account_id', sa.Integer(), nullable=False),
        
        # 업로드 통계
        sa.Column('total_uploads', sa.Integer(), server_default='0', nullable=False),
        sa.Column('successful_uploads', sa.Integer(), server_default='0', nullable=False),
        sa.Column('failed_uploads', sa.Integer(), server_default='0', nullable=False),
        
        # 마지막 활동
        sa.Column('last_upload_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_upload_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failed_upload_at', sa.DateTime(timezone=True), nullable=True),
        
        # 에러 추적
        sa.Column('consecutive_failures', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error_message', sa.Text(), nullable=True),
        
        # 상태 변경 이력
        sa.Column('status_changes', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['platform_account_id'], ['platform_accounts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('platform_account_id', name='uq_stats_platform_account'),
    )
    
    op.create_index('ix_platform_account_stats_account_id', 'platform_account_stats', ['platform_account_id'])
    
    # ==================== 7. Backup old tables ====================
    # Rename user_platform_credentials to _backup
    op.rename_table('user_platform_credentials', 'user_platform_credentials_backup')
    
    print("✅ SIM-centered architecture migration completed!")
    print("⚠️  Manual steps required:")
    print("  1. Migrate data from user_platform_credentials_backup to platform_accounts")
    print("  2. Update agents with sim_id")
    print("  3. Update upload_quotas with platform_account_id")
    print("  4. Test thoroughly before dropping backup tables")


def downgrade() -> None:
    """Rollback SIM-centered architecture changes"""
    
    # Restore old table
    op.rename_table('user_platform_credentials_backup', 'user_platform_credentials')
    
    # Drop new tables
    op.drop_table('platform_account_stats')
    op.drop_table('platform_accounts')
    op.drop_table('sim_cards')
    
    # Remove columns from existing tables
    op.drop_index('ix_jobs_target_sim_id', 'jobs')
    op.drop_constraint('fk_jobs_target_sim', 'jobs', type_='foreignkey')
    op.drop_column('jobs', 'target_sim_id')
    
    op.drop_index('ix_upload_quotas_platform_account_id', 'upload_quotas')
    op.drop_constraint('fk_upload_quotas_account', 'upload_quotas', type_='foreignkey')
    op.drop_constraint('uq_quota_platform_account', 'upload_quotas', type_='unique')
    op.drop_column('upload_quotas', 'platform_account_id')
    
    # Restore old constraint
    op.create_unique_constraint('uq_user_platform_quota', 'upload_quotas', ['user_id', 'platform_id'])
    
    op.drop_index('ix_agents_sim_id', 'agents')
    op.drop_constraint('uq_agents_sim_id', 'agents', type_='unique')
    op.drop_constraint('fk_agents_sim_id', 'agents', type_='foreignkey')
    op.drop_column('agents', 'sim_id')
    
    print("✅ Rollback completed!")
