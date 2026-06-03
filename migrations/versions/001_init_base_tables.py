"""init base tables

Revision ID: 001
Revises:
Create Date: 2026-05-27

"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # enterprise
    op.create_table(
        'enterprise',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('enterprise_name', sa.String(200), nullable=False),
        sa.Column('credit_code', sa.String(64), nullable=False),
        sa.Column('legal_person_name', sa.String(100), nullable=False),
        sa.Column('legal_person_id_no', sa.String(128), nullable=False),
        sa.Column('legal_person_mobile', sa.String(64), nullable=False),
        sa.Column('industry_code', sa.String(64), nullable=True),
        sa.Column('industry_name', sa.String(100), nullable=True),
        sa.Column('region_code', sa.String(32), nullable=True),
        sa.Column('region_name', sa.String(100), nullable=True),
        sa.Column('auth_source', sa.String(50), nullable=False, server_default='MOCK'),
        sa.Column('auth_account_id', sa.String(100), nullable=True),
        sa.Column('meeting_no_show_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meeting_booking_disabled', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('last_login_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('credit_code', name='uq_enterprise_credit_code'),
    )
    op.create_index('ix_enterprise_region_code', 'enterprise', ['region_code'])
    op.create_index('ix_enterprise_auth_account_id', 'enterprise', ['auth_account_id'])

    # service_center
    op.create_table(
        'service_center',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('center_name', sa.String(200), nullable=False),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('address', sa.String(300), nullable=True),
        sa.Column('contact_name', sa.String(100), nullable=True),
        sa.Column('contact_phone', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ENABLED'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_service_center_region_code', 'service_center', ['region_code'])

    # sys_user_snapshot
    op.create_table(
        'sys_user_snapshot',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('platform_user_id', sa.String(100), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('real_name', sa.String(100), nullable=False),
        sa.Column('mobile', sa.String(64), nullable=True),
        sa.Column('department_id', sa.String(100), nullable=False),
        sa.Column('department_name', sa.String(200), nullable=False),
        sa.Column('region_code', sa.String(32), nullable=False),
        sa.Column('region_name', sa.String(100), nullable=False),
        sa.Column('role_codes', sa.String(500), nullable=False),
        sa.Column('role_names', sa.String(500), nullable=True),
        sa.Column('data_scope', sa.String(50), nullable=False),
        sa.Column('last_login_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('platform_user_id', name='uq_sys_user_platform_user_id'),
    )
    op.create_index('ix_sys_user_snapshot_region_code', 'sys_user_snapshot', ['region_code'])
    op.create_index('ix_sys_user_snapshot_department_id', 'sys_user_snapshot', ['department_id'])

    # sys_dictionary
    op.create_table(
        'sys_dictionary',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('dict_type', sa.String(100), nullable=False),
        sa.Column('dict_code', sa.String(100), nullable=False),
        sa.Column('dict_label', sa.String(200), nullable=False),
        sa.Column('dict_value', sa.String(200), nullable=True),
        sa.Column('sort_no', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('enabled', sa.SmallInteger(), nullable=False, server_default='1'),
        sa.Column('parent_code', sa.String(100), nullable=True),
        sa.Column('extra_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dict_type', 'dict_code', name='uq_sys_dictionary_type_code'),
    )
    op.create_index('ix_sys_dictionary_dict_type', 'sys_dictionary', ['dict_type'])

    # sys_attachment
    op.create_table(
        'sys_attachment',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('business_type', sa.String(50), nullable=False),
        sa.Column('business_id', sa.BigInteger(), nullable=True),
        sa.Column('file_category', sa.String(50), nullable=True),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('stored_name', sa.String(255), nullable=False),
        sa.Column('file_ext', sa.String(20), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('uploaded_by_type', sa.String(20), nullable=False),
        sa.Column('uploaded_by_id', sa.String(100), nullable=False),
        sa.Column('uploaded_by_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sys_attachment_business', 'sys_attachment', ['business_type', 'business_id'])

    # sys_message_record
    op.create_table(
        'sys_message_record',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('business_type', sa.String(50), nullable=True),
        sa.Column('business_id', sa.BigInteger(), nullable=True),
        sa.Column('receiver_type', sa.String(30), nullable=False),
        sa.Column('receiver_id', sa.String(100), nullable=False),
        sa.Column('receiver_name', sa.String(100), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('channel', sa.String(50), nullable=False, server_default='SYSTEM'),
        sa.Column('send_status', sa.String(30), nullable=False, server_default='SENT'),
        sa.Column('send_time', sa.DateTime(), nullable=True),
        sa.Column('read_status', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.Column('read_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sys_message_record_receiver', 'sys_message_record', ['receiver_type', 'receiver_id'])
    op.create_index('ix_sys_message_record_business', 'sys_message_record', ['business_type', 'business_id'])

    # sys_evaluation
    op.create_table(
        'sys_evaluation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('business_type', sa.String(50), nullable=False),
        sa.Column('business_id', sa.BigInteger(), nullable=False),
        sa.Column('enterprise_id', sa.BigInteger(), nullable=False),
        sa.Column('satisfaction', sa.String(50), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('resolved_flag', sa.SmallInteger(), nullable=True),
        sa.Column('comment', sa.String(1000), nullable=True),
        sa.Column('evaluate_time', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sys_evaluation_business', 'sys_evaluation', ['business_type', 'business_id'])
    op.create_index('ix_sys_evaluation_enterprise_id', 'sys_evaluation', ['enterprise_id'])

    # sys_operation_log
    op.create_table(
        'sys_operation_log',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('operator_type', sa.String(30), nullable=False),
        sa.Column('operator_id', sa.String(100), nullable=False),
        sa.Column('operator_name', sa.String(100), nullable=False),
        sa.Column('business_type', sa.String(50), nullable=True),
        sa.Column('business_id', sa.BigInteger(), nullable=True),
        sa.Column('operation_type', sa.String(100), nullable=False),
        sa.Column('operation_content', sa.Text(), nullable=True),
        sa.Column('before_status', sa.String(50), nullable=True),
        sa.Column('after_status', sa.String(50), nullable=True),
        sa.Column('ip_address', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_sys_operation_log_operator', 'sys_operation_log', ['operator_type', 'operator_id'])
    op.create_index('ix_sys_operation_log_business', 'sys_operation_log', ['business_type', 'business_id'])
    op.create_index('ix_sys_operation_log_operation_type', 'sys_operation_log', ['operation_type'])


def downgrade() -> None:
    op.drop_table('sys_operation_log')
    op.drop_table('sys_evaluation')
    op.drop_table('sys_message_record')
    op.drop_table('sys_attachment')
    op.drop_table('sys_dictionary')
    op.drop_table('sys_user_snapshot')
    op.drop_table('service_center')
    op.drop_table('enterprise')
