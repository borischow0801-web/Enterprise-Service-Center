"""新增 sys_daily_serial 表：Appeal/MeetingRoomBooking/GovMeetingApply 三处
按日流水号生成的并发安全计数器（详见 app/utils/serial_no.py）。原先的"查询
当日最大编号再 +1"方式在多 worker/多容器下存在竞态，改为对本表做原子
UPDATE 自增。不修改、不迁移任何历史业务编号数据，仅新增这一张纯计数表。

Revision ID: 011_sys_daily_serial
Revises: 010_enterprise_identity
"""
from alembic import op
import sqlalchemy as sa

revision = '011_sys_daily_serial'
down_revision = '010_enterprise_identity'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sys_daily_serial',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('business_type', sa.String(30), nullable=False),
        sa.Column('business_date', sa.Date(), nullable=False),
        sa.Column('current_value', sa.Integer(), nullable=False, server_default='0'),
        sa.UniqueConstraint('business_type', 'business_date', name='uq_sys_daily_serial_type_date'),
    )


def downgrade():
    op.drop_table('sys_daily_serial')
