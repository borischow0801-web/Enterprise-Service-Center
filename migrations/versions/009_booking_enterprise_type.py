"""meeting_room_booking 增加申请主体类型

Revision ID: 009_booking_enterprise_type
Revises: 008_meeting_room_image
"""
from alembic import op
import sqlalchemy as sa

revision = '009_booking_enterprise_type'
down_revision = '008_meeting_room_image'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'meeting_room_booking',
        sa.Column('enterprise_type', sa.String(100), nullable=True),
    )
    op.add_column(
        'meeting_room_booking',
        sa.Column('enterprise_type_name', sa.String(200), nullable=True),
    )


def downgrade():
    op.drop_column('meeting_room_booking', 'enterprise_type_name')
    op.drop_column('meeting_room_booking', 'enterprise_type')
