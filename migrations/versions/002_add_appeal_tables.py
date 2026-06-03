"""add appeal tables

Revision ID: 002
Revises: 001
Create Date: 2026-05-27

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'appeal_main',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('appeal_no', sa.String(64), nullable=False),
        sa.Column('enterprise_id', sa.BigInteger(), nullable=False),
        sa.Column('enterprise_name', sa.String(200), nullable=False),
        sa.Column('credit_code', sa.String(64), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('contact_name', sa.String(100), nullable=False),
        sa.Column('contact_phone', sa.String(64), nullable=False),
        sa.Column('industry_code', sa.String(64), nullable=True),
        sa.Column('industry_name', sa.String(100), nullable=True),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('service_center_id', sa.BigInteger(), nullable=True),
        sa.Column('appeal_type_code', sa.String(100), nullable=True),
        sa.Column('appeal_type_name', sa.String(100), nullable=True),
        sa.Column('urgency_level', sa.String(50), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('handle_mode', sa.String(50), nullable=True),
        sa.Column('responsible_dept_id', sa.String(100), nullable=True),
        sa.Column('responsible_dept_name', sa.String(200), nullable=True),
        sa.Column('reply_deadline', sa.DateTime(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('accepted_at', sa.DateTime(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('appeal_no', name='uq_appeal_main_appeal_no'),
    )
    op.create_index('ix_appeal_main_enterprise_id', 'appeal_main', ['enterprise_id'])
    op.create_index('ix_appeal_main_credit_code', 'appeal_main', ['credit_code'])
    op.create_index('ix_appeal_main_region_code', 'appeal_main', ['region_code'])
    op.create_index('ix_appeal_main_status', 'appeal_main', ['status'])
    op.create_index('ix_appeal_main_responsible_dept_id', 'appeal_main', ['responsible_dept_id'])
    op.create_index('ix_appeal_main_submitted_at', 'appeal_main', ['submitted_at'])

    op.create_table(
        'appeal_record',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('appeal_id', sa.BigInteger(), nullable=False),
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
    op.create_index('ix_appeal_record_appeal_id', 'appeal_record', ['appeal_id'])
    op.create_index('ix_appeal_record_action_type', 'appeal_record', ['action_type'])
    op.create_index('ix_appeal_record_operator', 'appeal_record', ['operator_type', 'operator_id'])

    op.create_table(
        'appeal_assignment',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('appeal_id', sa.BigInteger(), nullable=False),
        sa.Column('assigned_dept_id', sa.String(100), nullable=False),
        sa.Column('assigned_dept_name', sa.String(200), nullable=False),
        sa.Column('assigned_user_id', sa.String(100), nullable=True),
        sa.Column('assigned_user_name', sa.String(100), nullable=True),
        sa.Column('assign_opinion', sa.Text(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('reply_content', sa.Text(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_appeal_assignment_appeal_id', 'appeal_assignment', ['appeal_id'])
    op.create_index('ix_appeal_assignment_assigned_dept_id', 'appeal_assignment', ['assigned_dept_id'])
    op.create_index('ix_appeal_assignment_status', 'appeal_assignment', ['status'])

    op.create_table(
        'appeal_followup',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('appeal_id', sa.BigInteger(), nullable=False),
        sa.Column('evaluation_id', sa.BigInteger(), nullable=True),
        sa.Column('responsible_dept_id', sa.String(100), nullable=True),
        sa.Column('responsible_dept_name', sa.String(200), nullable=True),
        sa.Column('followup_status', sa.String(50), nullable=False),
        sa.Column('followup_method', sa.String(50), nullable=True),
        sa.Column('followup_content', sa.Text(), nullable=True),
        sa.Column('followup_result', sa.Text(), nullable=True),
        sa.Column('followup_user_id', sa.String(100), nullable=False),
        sa.Column('followup_user_name', sa.String(100), nullable=False),
        sa.Column('followup_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_appeal_followup_appeal_id', 'appeal_followup', ['appeal_id'])
    op.create_index('ix_appeal_followup_evaluation_id', 'appeal_followup', ['evaluation_id'])
    op.create_index('ix_appeal_followup_responsible_dept_id', 'appeal_followup', ['responsible_dept_id'])


def downgrade() -> None:
    op.drop_table('appeal_followup')
    op.drop_table('appeal_assignment')
    op.drop_table('appeal_record')
    op.drop_table('appeal_main')
