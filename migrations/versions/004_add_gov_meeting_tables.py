"""add gov meeting tables

Revision ID: 004
Revises: 003
Create Date: 2026-05-27

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'gov_meeting_apply',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('apply_no', sa.String(64), nullable=False),
        sa.Column('enterprise_id', sa.BigInteger(), nullable=False),
        sa.Column('enterprise_name', sa.String(200), nullable=False),
        sa.Column('credit_code', sa.String(64), nullable=False),
        sa.Column('contact_name', sa.String(100), nullable=False),
        sa.Column('contact_phone', sa.String(64), nullable=False),
        sa.Column('topic_code', sa.String(100), nullable=True),
        sa.Column('topic_name', sa.String(100), nullable=True),
        sa.Column('meeting_level', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('commitment_checked', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('service_center_id', sa.BigInteger(), nullable=True),
        sa.Column('service_center_name', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('reject_reason_code', sa.String(100), nullable=True),
        sa.Column('reject_reason_name', sa.String(200), nullable=True),
        sa.Column('reject_opinion', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('arranged_at', sa.DateTime(), nullable=True),
        sa.Column('meeting_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('apply_no', name='uq_gov_meeting_apply_no'),
    )
    op.create_index('ix_gov_meeting_apply_enterprise_id', 'gov_meeting_apply', ['enterprise_id'])
    op.create_index('ix_gov_meeting_apply_credit_code', 'gov_meeting_apply', ['credit_code'])
    op.create_index('ix_gov_meeting_apply_region_code', 'gov_meeting_apply', ['region_code'])
    op.create_index('ix_gov_meeting_apply_status', 'gov_meeting_apply', ['status'])
    op.create_index('ix_gov_meeting_apply_submitted_at', 'gov_meeting_apply', ['submitted_at'])

    op.create_table(
        'gov_meeting_audit',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('apply_id', sa.BigInteger(), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('action_name', sa.String(100), nullable=False),
        sa.Column('before_status', sa.String(50), nullable=True),
        sa.Column('after_status', sa.String(50), nullable=True),
        sa.Column('opinion', sa.Text(), nullable=True),
        sa.Column('operator_type', sa.String(30), nullable=False),
        sa.Column('operator_id', sa.String(100), nullable=False),
        sa.Column('operator_name', sa.String(100), nullable=False),
        sa.Column('operator_dept_id', sa.String(100), nullable=True),
        sa.Column('operator_dept_name', sa.String(200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_gov_meeting_audit_apply_id', 'gov_meeting_audit', ['apply_id'])
    op.create_index('ix_gov_meeting_audit_action_type', 'gov_meeting_audit', ['action_type'])

    op.create_table(
        'gov_meeting_arrangement',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('apply_id', sa.BigInteger(), nullable=False),
        sa.Column('meeting_date', sa.DateTime(), nullable=True),
        sa.Column('meeting_place', sa.String(300), nullable=True),
        sa.Column('meeting_method', sa.String(50), nullable=True),
        sa.Column('gov_contact_name', sa.String(100), nullable=True),
        sa.Column('gov_contact_phone', sa.String(64), nullable=True),
        sa.Column('remark', sa.Text(), nullable=True),
        sa.Column('confirmed_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_gov_meeting_arrangement_apply_id', 'gov_meeting_arrangement', ['apply_id'])

    op.create_table(
        'gov_meeting_participant',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('arrangement_id', sa.BigInteger(), nullable=False),
        sa.Column('apply_id', sa.BigInteger(), nullable=False),
        sa.Column('participant_type', sa.String(30), nullable=False),
        sa.Column('participant_name', sa.String(100), nullable=False),
        sa.Column('participant_title', sa.String(200), nullable=True),
        sa.Column('sort_no', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_gov_meeting_participant_arrangement_id', 'gov_meeting_participant', ['arrangement_id'])
    op.create_index('ix_gov_meeting_participant_apply_id', 'gov_meeting_participant', ['apply_id'])

    op.create_table(
        'gov_meeting_record',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('apply_id', sa.BigInteger(), nullable=False),
        sa.Column('arrangement_id', sa.BigInteger(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('conclusions', sa.Text(), nullable=True),
        sa.Column('follow_up_items', sa.Text(), nullable=True),
        sa.Column('recorder_id', sa.String(100), nullable=False),
        sa.Column('recorder_name', sa.String(100), nullable=False),
        sa.Column('record_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_gov_meeting_record_apply_id', 'gov_meeting_record', ['apply_id'])
    op.create_index('ix_gov_meeting_record_arrangement_id', 'gov_meeting_record', ['arrangement_id'])


def downgrade() -> None:
    op.drop_table('gov_meeting_record')
    op.drop_table('gov_meeting_participant')
    op.drop_table('gov_meeting_arrangement')
    op.drop_table('gov_meeting_audit')
    op.drop_table('gov_meeting_apply')
