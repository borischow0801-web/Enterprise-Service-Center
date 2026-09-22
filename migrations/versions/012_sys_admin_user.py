"""新增 sys_admin_user 表：管理端统一身份认证（BSPPLUS）改造的正式管理员账号/
角色分配表。与 sys_user_snapshot（admin_mock_login 专用的开发/测试身份快照）
完全分离——本表的 role_codes/data_scope/region_code/department_id 只由管理员
管理界面写入，登录流程（BSP 认证成功后）只读取、不覆盖。不迁移、不触碰
sys_user_snapshot 的任何历史数据。

Revision ID: 012_sys_admin_user
Revises: 011_sys_daily_serial
"""
from alembic import op
import sqlalchemy as sa

revision = '012_sys_admin_user'
down_revision = '011_sys_daily_serial'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sys_admin_user',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('bsp_user_id', sa.String(100), nullable=True),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('real_name', sa.String(100), nullable=False),
        sa.Column('mobile', sa.String(64), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='ACTIVE'),
        sa.Column('role_codes', sa.String(500), nullable=False, server_default=''),
        sa.Column('data_scope', sa.String(50), nullable=False, server_default='SELF'),
        sa.Column('region_code', sa.String(32), nullable=True),
        sa.Column('region_name', sa.String(100), nullable=True),
        sa.Column('department_id', sa.String(100), nullable=True),
        sa.Column('department_name', sa.String(200), nullable=True),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_flag', sa.SmallInteger(), nullable=False, server_default='0'),
        sa.UniqueConstraint('bsp_user_id', name='uq_sys_admin_user_bsp_user_id'),
        sa.UniqueConstraint('username', name='uq_sys_admin_user_username'),
    )
    op.create_index('ix_sys_admin_user_bsp_user_id', 'sys_admin_user', ['bsp_user_id'])
    op.create_index('ix_sys_admin_user_username', 'sys_admin_user', ['username'])
    op.create_index('ix_sys_admin_user_region_code', 'sys_admin_user', ['region_code'])
    op.create_index('ix_sys_admin_user_department_id', 'sys_admin_user', ['department_id'])


def downgrade():
    op.drop_index('ix_sys_admin_user_department_id', table_name='sys_admin_user')
    op.drop_index('ix_sys_admin_user_region_code', table_name='sys_admin_user')
    op.drop_index('ix_sys_admin_user_username', table_name='sys_admin_user')
    op.drop_index('ix_sys_admin_user_bsp_user_id', table_name='sys_admin_user')
    op.drop_table('sys_admin_user')
