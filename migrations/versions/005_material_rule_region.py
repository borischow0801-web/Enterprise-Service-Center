"""material_rule_region: add region/service_center fields to material rule table

Revision ID: 005_material_rule_region
Revises: 004_add_gov_meeting_tables
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = '005_material_rule_region'
down_revision = '004'
branch_labels = None
depends_on = None


def _column_exists(conn, table, column):
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
    ), {"t": table, "c": column})
    return result.scalar() > 0


def _index_exists(conn, table, index):
    result = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.STATISTICS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
    ), {"t": table, "i": index})
    return result.scalar() > 0


def upgrade():
    conn = op.get_bind()
    tbl = 'meeting_room_material_rule'

    # Add columns (idempotent)
    for col_def in [
        ('region_code', 'VARCHAR(32)'),
        ('region_name', 'VARCHAR(100)'),
        ('service_center_id', 'BIGINT'),
        ('service_center_name', 'VARCHAR(100)'),
        ('sort_no', 'INT NOT NULL DEFAULT 0'),
    ]:
        if not _column_exists(conn, tbl, col_def[0]):
            conn.execute(sa.text(f'ALTER TABLE {tbl} ADD COLUMN {col_def[0]} {col_def[1]}'))

    # Create new indexes (idempotent)
    for idx_name, cols in [
        ('ix_mrmr_region_code', 'region_code'),
        ('ix_mrmr_service_center_id', 'service_center_id'),
        ('ix_mrmr_region_center', 'region_code, service_center_id'),
        ('ix_mrmr_material_code', 'material_code'),
        ('ix_mrmr_room_id', 'room_id'),
        ('ix_mrmr_enterprise_type', 'enterprise_type'),
    ]:
        if not _index_exists(conn, tbl, idx_name):
            conn.execute(sa.text(f'CREATE INDEX {idx_name} ON {tbl} ({cols})'))

    # Drop old indexes
    for old_idx in [
        'ix_meeting_room_material_rule_room_id',
        'ix_meeting_room_material_rule_enterprise_type',
        'ix_meeting_room_material_rule_material_code',
    ]:
        if _index_exists(conn, tbl, old_idx):
            conn.execute(sa.text(f'DROP INDEX {old_idx} ON {tbl}'))

    # Back-fill region info from meeting_room table (MySQL JOIN syntax)
    conn.execute(sa.text("""
        UPDATE meeting_room_material_rule mr
        JOIN meeting_room r ON mr.room_id = r.id
        SET mr.region_code = r.region_code,
            mr.region_name = r.region_name,
            mr.service_center_id = r.service_center_id,
            mr.service_center_name = r.service_center_name
        WHERE mr.region_code IS NULL
    """))


def downgrade():
    op.drop_index('ix_mrmr_region_code', 'meeting_room_material_rule')
    op.drop_index('ix_mrmr_service_center_id', 'meeting_room_material_rule')
    op.drop_index('ix_mrmr_region_center', 'meeting_room_material_rule')
    op.drop_index('ix_mrmr_material_code', 'meeting_room_material_rule')
    op.drop_index('ix_mrmr_room_id', 'meeting_room_material_rule')
    op.drop_index('ix_mrmr_enterprise_type', 'meeting_room_material_rule')
    op.drop_column('meeting_room_material_rule', 'region_code')
    op.drop_column('meeting_room_material_rule', 'region_name')
    op.drop_column('meeting_room_material_rule', 'service_center_id')
    op.drop_column('meeting_room_material_rule', 'service_center_name')
    op.drop_column('meeting_room_material_rule', 'sort_no')
