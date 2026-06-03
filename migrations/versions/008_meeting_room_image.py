"""meeting_room_image: 会议室多图

Revision ID: 008_meeting_room_image
Revises: 007_gm_enterprise_fields
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = '008_meeting_room_image'
down_revision = '007_gm_enterprise_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'meeting_room_image',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('attachment_id', sa.BigInteger(), nullable=False),
        sa.Column('is_cover', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('sort_no', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_image_room_id', 'meeting_room_image', ['room_id'])


def downgrade():
    op.drop_index('ix_meeting_room_image_room_id', table_name='meeting_room_image')
    op.drop_table('meeting_room_image')
