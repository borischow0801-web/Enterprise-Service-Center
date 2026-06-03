"""add meeting room tables

Revision ID: 003
Revises: 002
Create Date: 2026-05-27

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'meeting_room',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_name', sa.String(200), nullable=False),
        sa.Column('room_type', sa.String(100), nullable=True),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('service_center_id', sa.BigInteger(), nullable=True),
        sa.Column('service_center_name', sa.String(100), nullable=True),
        sa.Column('address', sa.String(300), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('facilities', sa.String(1000), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('cover_attachment_id', sa.BigInteger(), nullable=True),
        sa.Column('booking_notice', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='ENABLED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_region_code', 'meeting_room', ['region_code'])
    op.create_index('ix_meeting_room_service_center_id', 'meeting_room', ['service_center_id'])
    op.create_index('ix_meeting_room_status', 'meeting_room', ['status'])

    op.create_table(
        'meeting_room_open_rule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('weekday', sa.Integer(), nullable=False),
        sa.Column('open_flag', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('start_time', sa.String(10), nullable=True),
        sa.Column('end_time', sa.String(10), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_open_rule_room_id', 'meeting_room_open_rule', ['room_id'])
    op.create_index('ix_meeting_room_open_rule_weekday', 'meeting_room_open_rule', ['weekday'])

    op.create_table(
        'meeting_room_special_date',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('service_center_id', sa.BigInteger(), nullable=True),
        sa.Column('special_date', sa.Date(), nullable=False),
        sa.Column('date_type', sa.String(50), nullable=False),
        sa.Column('open_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('reason', sa.String(300), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_special_date_region_code', 'meeting_room_special_date', ['region_code'])
    op.create_index('ix_meeting_room_special_date_service_center_id', 'meeting_room_special_date', ['service_center_id'])
    op.create_index('ix_meeting_room_special_date_special_date', 'meeting_room_special_date', ['special_date'])

    op.create_table(
        'meeting_room_occupy',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('occupy_title', sa.String(200), nullable=False),
        sa.Column('occupy_reason', sa.String(500), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(100), nullable=False),
        sa.Column('created_by_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_occupy_room_id', 'meeting_room_occupy', ['room_id'])
    op.create_index('ix_meeting_room_occupy_start_time', 'meeting_room_occupy', ['start_time'])
    op.create_index('ix_meeting_room_occupy_end_time', 'meeting_room_occupy', ['end_time'])

    op.create_table(
        'meeting_room_material_rule',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=True),
        sa.Column('enterprise_type', sa.String(100), nullable=True),
        sa.Column('material_name', sa.String(200), nullable=False),
        sa.Column('material_code', sa.String(100), nullable=False),
        sa.Column('required_flag', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('template_attachment_id', sa.BigInteger(), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('enabled', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_material_rule_room_id', 'meeting_room_material_rule', ['room_id'])
    op.create_index('ix_meeting_room_material_rule_enterprise_type', 'meeting_room_material_rule', ['enterprise_type'])
    op.create_index('ix_meeting_room_material_rule_material_code', 'meeting_room_material_rule', ['material_code'])

    op.create_table(
        'meeting_room_booking',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('booking_no', sa.String(64), nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('room_name', sa.String(200), nullable=False),
        sa.Column('enterprise_id', sa.BigInteger(), nullable=False),
        sa.Column('enterprise_name', sa.String(200), nullable=False),
        sa.Column('credit_code', sa.String(64), nullable=False),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('service_center_id', sa.BigInteger(), nullable=True),
        sa.Column('meeting_subject', sa.String(200), nullable=False),
        sa.Column('participant_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('contact_name', sa.String(100), nullable=False),
        sa.Column('contact_phone', sa.String(64), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('support_items', sa.String(1000), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('cancel_reason', sa.String(500), nullable=True),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_no', name='uq_meeting_room_booking_no'),
    )
    op.create_index('ix_meeting_room_booking_room_id', 'meeting_room_booking', ['room_id'])
    op.create_index('ix_meeting_room_booking_enterprise_id', 'meeting_room_booking', ['enterprise_id'])
    op.create_index('ix_meeting_room_booking_credit_code', 'meeting_room_booking', ['credit_code'])
    op.create_index('ix_meeting_room_booking_region_code', 'meeting_room_booking', ['region_code'])
    op.create_index('ix_meeting_room_booking_service_center_id', 'meeting_room_booking', ['service_center_id'])
    op.create_index('ix_meeting_room_booking_status', 'meeting_room_booking', ['status'])
    op.create_index('ix_meeting_room_booking_start_time', 'meeting_room_booking', ['start_time'])
    op.create_index('ix_meeting_room_booking_end_time', 'meeting_room_booking', ['end_time'])

    op.create_table(
        'meeting_room_booking_audit',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('booking_id', sa.BigInteger(), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('before_status', sa.String(50), nullable=True),
        sa.Column('after_status', sa.String(50), nullable=True),
        sa.Column('audit_opinion', sa.Text(), nullable=True),
        sa.Column('operator_id', sa.String(100), nullable=False),
        sa.Column('operator_name', sa.String(100), nullable=False),
        sa.Column('operator_dept_id', sa.String(100), nullable=True),
        sa.Column('operator_dept_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_booking_audit_booking_id', 'meeting_room_booking_audit', ['booking_id'])
    op.create_index('ix_meeting_room_booking_audit_action_type', 'meeting_room_booking_audit', ['action_type'])
    op.create_index('ix_meeting_room_booking_audit_operator_id', 'meeting_room_booking_audit', ['operator_id'])

    op.create_table(
        'meeting_room_usage',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('booking_id', sa.BigInteger(), nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('usage_status', sa.String(50), nullable=False),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('confirm_user_id', sa.String(100), nullable=True),
        sa.Column('confirm_user_name', sa.String(100), nullable=True),
        sa.Column('confirm_time', sa.DateTime(), nullable=True),
        sa.Column('remark', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_usage_booking_id', 'meeting_room_usage', ['booking_id'])
    op.create_index('ix_meeting_room_usage_room_id', 'meeting_room_usage', ['room_id'])
    op.create_index('ix_meeting_room_usage_usage_status', 'meeting_room_usage', ['usage_status'])

    op.create_table(
        'meeting_room_no_show',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('enterprise_id', sa.BigInteger(), nullable=False),
        sa.Column('enterprise_name', sa.String(200), nullable=False),
        sa.Column('credit_code', sa.String(64), nullable=False),
        sa.Column('booking_id', sa.BigInteger(), nullable=False),
        sa.Column('room_id', sa.BigInteger(), nullable=False),
        sa.Column('no_show_time', sa.DateTime(), nullable=False),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('operator_id', sa.String(100), nullable=False),
        sa.Column('operator_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_meeting_room_no_show_enterprise_id', 'meeting_room_no_show', ['enterprise_id'])
    op.create_index('ix_meeting_room_no_show_credit_code', 'meeting_room_no_show', ['credit_code'])
    op.create_index('ix_meeting_room_no_show_booking_id', 'meeting_room_no_show', ['booking_id'])
    op.create_index('ix_meeting_room_no_show_room_id', 'meeting_room_no_show', ['room_id'])


def downgrade() -> None:
    op.drop_index('ix_meeting_room_no_show_room_id', table_name='meeting_room_no_show')
    op.drop_index('ix_meeting_room_no_show_booking_id', table_name='meeting_room_no_show')
    op.drop_index('ix_meeting_room_no_show_credit_code', table_name='meeting_room_no_show')
    op.drop_index('ix_meeting_room_no_show_enterprise_id', table_name='meeting_room_no_show')
    op.drop_table('meeting_room_no_show')

    op.drop_index('ix_meeting_room_usage_usage_status', table_name='meeting_room_usage')
    op.drop_index('ix_meeting_room_usage_room_id', table_name='meeting_room_usage')
    op.drop_index('ix_meeting_room_usage_booking_id', table_name='meeting_room_usage')
    op.drop_table('meeting_room_usage')

    op.drop_index('ix_meeting_room_booking_audit_operator_id', table_name='meeting_room_booking_audit')
    op.drop_index('ix_meeting_room_booking_audit_action_type', table_name='meeting_room_booking_audit')
    op.drop_index('ix_meeting_room_booking_audit_booking_id', table_name='meeting_room_booking_audit')
    op.drop_table('meeting_room_booking_audit')

    op.drop_index('ix_meeting_room_booking_end_time', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_start_time', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_status', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_service_center_id', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_region_code', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_credit_code', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_enterprise_id', table_name='meeting_room_booking')
    op.drop_index('ix_meeting_room_booking_room_id', table_name='meeting_room_booking')
    op.drop_table('meeting_room_booking')

    op.drop_index('ix_meeting_room_material_rule_material_code', table_name='meeting_room_material_rule')
    op.drop_index('ix_meeting_room_material_rule_enterprise_type', table_name='meeting_room_material_rule')
    op.drop_index('ix_meeting_room_material_rule_room_id', table_name='meeting_room_material_rule')
    op.drop_table('meeting_room_material_rule')

    op.drop_index('ix_meeting_room_occupy_end_time', table_name='meeting_room_occupy')
    op.drop_index('ix_meeting_room_occupy_start_time', table_name='meeting_room_occupy')
    op.drop_index('ix_meeting_room_occupy_room_id', table_name='meeting_room_occupy')
    op.drop_table('meeting_room_occupy')

    op.drop_index('ix_meeting_room_special_date_special_date', table_name='meeting_room_special_date')
    op.drop_index('ix_meeting_room_special_date_service_center_id', table_name='meeting_room_special_date')
    op.drop_index('ix_meeting_room_special_date_region_code', table_name='meeting_room_special_date')
    op.drop_table('meeting_room_special_date')

    op.drop_index('ix_meeting_room_open_rule_weekday', table_name='meeting_room_open_rule')
    op.drop_index('ix_meeting_room_open_rule_room_id', table_name='meeting_room_open_rule')
    op.drop_table('meeting_room_open_rule')

    op.drop_index('ix_meeting_room_status', table_name='meeting_room')
    op.drop_index('ix_meeting_room_service_center_id', table_name='meeting_room')
    op.drop_index('ix_meeting_room_region_code', table_name='meeting_room')
    op.drop_table('meeting_room')
