"""Add worksheet architecture tables

Revision ID: 0002_worksheet_arch
Revises: aaa407338e4a
Create Date: 2026-04-22

"""
from alembic import op
import sqlalchemy as sa

revision = '0002_worksheet_arch'
down_revision = 'aaa407338e4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── worksheets ─────────────────────────────────────────────────────────────
    op.create_table(
        'worksheets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_shared', sa.Boolean(), default=False),
        sa.Column('sharing_type', sa.String(50), default='private'),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('source_id', sa.String(255), nullable=True),
        sa.Column('total_rows', sa.Integer(), default=0),
        sa.Column('column_count', sa.Integer(), default=0),
        sa.Column('size_bytes', sa.Integer(), default=0),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_worksheets_owner', 'worksheets', ['owner_id'])
    op.create_index('idx_worksheets_shared', 'worksheets', ['is_shared'])
    op.create_index('idx_worksheets_created', 'worksheets', ['created_at'])

    # ── worksheet_columns ──────────────────────────────────────────────────────
    op.create_table(
        'worksheet_columns',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worksheet_id', sa.String(), sa.ForeignKey('worksheets.id'), nullable=False),
        sa.Column('column_name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('data_type', sa.String(50), nullable=True),
        sa.Column('null_count', sa.Integer(), default=0),
        sa.Column('unique_count', sa.Integer(), default=0),
        sa.Column('min_value', sa.Text(), nullable=True),
        sa.Column('max_value', sa.Text(), nullable=True),
        sa.Column('column_order', sa.Integer(), nullable=True),
        sa.Column('is_indexed', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ws_col', 'worksheet_columns', ['worksheet_id', 'column_name'])

    # ── worksheet_data ─────────────────────────────────────────────────────────
    op.create_table(
        'worksheet_data',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worksheet_id', sa.String(), sa.ForeignKey('worksheets.id'), nullable=False),
        sa.Column('row_number', sa.Integer(), nullable=False),
        sa.Column('data_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_ws_data_ws', 'worksheet_data', ['worksheet_id'])
    op.create_index('idx_ws_data_row', 'worksheet_data', ['worksheet_id', 'row_number'])

    # ── worksheet_permissions ──────────────────────────────────────────────────
    op.create_table(
        'worksheet_permissions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worksheet_id', sa.String(), sa.ForeignKey('worksheets.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('permission_level', sa.String(50), default='view'),
        sa.Column('can_export', sa.Boolean(), default=True),
        sa.Column('can_share', sa.Boolean(), default=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('granted_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_perm_user', 'worksheet_permissions', ['user_id'])
    op.create_index('idx_perm_ws', 'worksheet_permissions', ['worksheet_id'])

    # ── data_import_queue ──────────────────────────────────────────────────────
    op.create_table(
        'data_import_queue',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worksheet_id', sa.String(), sa.ForeignKey('worksheets.id'), nullable=False, unique=True),
        sa.Column('status', sa.String(50), default='pending'),
        sa.Column('progress_percent', sa.Integer(), default=0),
        sa.Column('rows_processed', sa.Integer(), default=0),
        sa.Column('rows_failed', sa.Integer(), default=0),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # ── worksheet_transformations ──────────────────────────────────────────────
    op.create_table(
        'worksheet_transformations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('worksheet_id', sa.String(), sa.ForeignKey('worksheets.id'), nullable=False),
        sa.Column('transformation_type', sa.String(50), nullable=True),
        sa.Column('transformation_config', sa.JSON(), nullable=True),
        sa.Column('result_row_count', sa.Integer(), nullable=True),
        sa.Column('is_applied', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('worksheet_transformations')
    op.drop_table('data_import_queue')
    op.drop_table('worksheet_permissions')
    op.drop_table('worksheet_data')
    op.drop_table('worksheet_columns')
    op.drop_table('worksheets')
