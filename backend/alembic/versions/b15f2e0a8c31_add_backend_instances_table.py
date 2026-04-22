"""add backend_instances table

Revision ID: b15f2e0a8c31
Revises: 96d580b2024d
Create Date: 2026-04-22 10:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'b15f2e0a8c31'
down_revision = '96d580b2024d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'backend_instances',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('backend_id', sa.String(length=128), nullable=False),
        sa.Column('scheme', sa.String(length=16), nullable=False),
        sa.Column('local_ip', sa.String(length=64), nullable=True),
        sa.Column('local_port', sa.SmallInteger(), nullable=False),
        sa.Column('public_ip', sa.String(length=64), nullable=True),
        sa.Column('public_port', sa.SmallInteger(), nullable=True),
        sa.Column('base_url', sa.String(length=512), nullable=False),
        sa.Column('nat_detected', sa.Boolean(), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('extra', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backend_instances_backend_id'), 'backend_instances', ['backend_id'], unique=True)
    op.create_index(op.f('ix_backend_instances_last_seen'), 'backend_instances', ['last_seen'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_backend_instances_last_seen'), table_name='backend_instances')
    op.drop_index(op.f('ix_backend_instances_backend_id'), table_name='backend_instances')
    op.drop_table('backend_instances')
