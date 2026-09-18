"""新增 enterprise_identity 表（企业登录身份，与 enterprise 业务档案解耦），
企业自主注册（LOCAL 登录方式）第一步；enterprise.legal_person_* 三字段改为可空，
因为本地注册阶段收集的是"联系人"而非经核实的"法人"信息。

Revision ID: 010_enterprise_identity
Revises: 009_booking_enterprise_type
"""
from alembic import op
import sqlalchemy as sa

revision = '010_enterprise_identity'
down_revision = '009_booking_enterprise_type'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'enterprise_identity',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('enterprise_id', sa.BigInteger(), sa.ForeignKey('enterprise.id'), nullable=False),
        sa.Column('identity_type', sa.String(30), nullable=False),
        sa.Column('identifier', sa.String(128), nullable=False),
        sa.Column('credential_hash', sa.String(255), nullable=True),
        sa.Column('contact_name', sa.String(100), nullable=True),
        sa.Column('contact_mobile', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('last_login_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.UniqueConstraint('identity_type', 'identifier', name='uq_enterprise_identity_type_identifier'),
    )
    op.create_index(
        'ix_enterprise_identity_enterprise_id', 'enterprise_identity', ['enterprise_id']
    )

    # 法人三要素由 LOCAL 注册阶段无法采集，改为可空；已有数据不受影响（原值保留）。
    op.alter_column('enterprise', 'legal_person_name', existing_type=sa.String(100), nullable=True)
    op.alter_column('enterprise', 'legal_person_id_no', existing_type=sa.String(128), nullable=True)
    op.alter_column('enterprise', 'legal_person_mobile', existing_type=sa.String(64), nullable=True)


def downgrade():
    # 注意：若此时法人字段已存在 NULL 数据（LOCAL 注册产生的企业），
    # 下面两行 alter_column 会因为 NOT NULL 约束校验失败而报错——这是预期行为，
    # 降级前需要先手工回填或删除这些数据，不在本迁移脚本中做隐式数据处理。
    op.alter_column('enterprise', 'legal_person_mobile', existing_type=sa.String(64), nullable=False)
    op.alter_column('enterprise', 'legal_person_id_no', existing_type=sa.String(128), nullable=False)
    op.alter_column('enterprise', 'legal_person_name', existing_type=sa.String(100), nullable=False)

    op.drop_index('ix_enterprise_identity_enterprise_id', table_name='enterprise_identity')
    op.drop_table('enterprise_identity')
