"""gov_meeting_apply_enterprise_fields: add title/content/discussion/urgency/industry/address

Revision ID: 007_gov_meeting_apply_enterprise_fields
Revises: 006_gov_meeting_fields_extend
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = '007_gm_enterprise_fields'
down_revision = '006_gov_meeting_fields_extend'
branch_labels = None
depends_on = None


def _column_exists(conn, table, column):
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
    ), {"t": table, "c": column})
    return result.scalar() > 0


def upgrade():
    conn = op.get_bind()
    tbl = 'gov_meeting_apply'

    for col, definition in [
        ('title',             'VARCHAR(300)'),      # 约见申请标题
        ('meeting_content',   'TEXT'),               # 约见内容（企业端独立字段）
        ('discussion_item',   'TEXT'),               # 洽谈事项
        ('urgency_level',     'VARCHAR(50)'),        # 紧急程度
        ('industry_code',     'VARCHAR(100)'),       # 所属行业代码
        ('industry_name',     'VARCHAR(200)'),       # 所属行业名称
        ('registered_address','VARCHAR(500)'),       # 企业注册地址
    ]:
        if not _column_exists(conn, tbl, col):
            conn.execute(sa.text(f'ALTER TABLE {tbl} ADD COLUMN {col} {definition}'))


def downgrade():
    conn = op.get_bind()
    for col in ['title', 'meeting_content', 'discussion_item', 'urgency_level',
                'industry_code', 'industry_name', 'registered_address']:
        if _column_exists(conn, 'gov_meeting_apply', col):
            conn.execute(sa.text(f'ALTER TABLE gov_meeting_apply DROP COLUMN {col}'))
