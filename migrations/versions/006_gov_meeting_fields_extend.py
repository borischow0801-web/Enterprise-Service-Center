"""gov_meeting_fields_extend: add expected/final level to apply, start/end time & host dept to arrangement, dept/phone/role to participant

Revision ID: 006_gov_meeting_fields_extend
Revises: 005_material_rule_region
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa

revision = '006_gov_meeting_fields_extend'
down_revision = '005_material_rule_region'
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

    # ── gov_meeting_apply: split meeting_level into expected / final ──────────
    for col, definition in [
        ('expected_level_code', 'VARCHAR(100)'),
        ('expected_level_name', 'VARCHAR(200)'),
        ('final_level_code',    'VARCHAR(100)'),
        ('final_level_name',    'VARCHAR(200)'),
    ]:
        if not _column_exists(conn, 'gov_meeting_apply', col):
            conn.execute(sa.text(
                f'ALTER TABLE gov_meeting_apply ADD COLUMN {col} {definition}'
            ))

    # Back-fill expected_level from existing meeting_level
    conn.execute(sa.text("""
        UPDATE gov_meeting_apply
        SET expected_level_code = meeting_level,
            expected_level_name = meeting_level
        WHERE meeting_level IS NOT NULL
          AND expected_level_code IS NULL
    """))

    # ── gov_meeting_arrangement: start_time, end_time, host dept, notes ───────
    for col, definition in [
        ('start_time',      'DATETIME'),
        ('end_time',        'DATETIME'),
        ('host_dept_id',    'VARCHAR(100)'),
        ('host_dept_name',  'VARCHAR(200)'),
        ('notes',           'TEXT'),
    ]:
        if not _column_exists(conn, 'gov_meeting_arrangement', col):
            conn.execute(sa.text(
                f'ALTER TABLE gov_meeting_arrangement ADD COLUMN {col} {definition}'
            ))

    # ── gov_meeting_participant: dept, contact_phone, role ───────────────────
    for col, definition in [
        ('participant_dept_id',   'VARCHAR(100)'),
        ('participant_dept_name', 'VARCHAR(200)'),
        ('contact_phone',         'VARCHAR(64)'),
        ('role_name',             'VARCHAR(100)'),
    ]:
        if not _column_exists(conn, 'gov_meeting_participant', col):
            conn.execute(sa.text(
                f'ALTER TABLE gov_meeting_participant ADD COLUMN {col} {definition}'
            ))


def downgrade():
    conn = op.get_bind()

    for col in ['expected_level_code', 'expected_level_name', 'final_level_code', 'final_level_name']:
        if _column_exists(conn, 'gov_meeting_apply', col):
            conn.execute(sa.text(f'ALTER TABLE gov_meeting_apply DROP COLUMN {col}'))

    for col in ['start_time', 'end_time', 'host_dept_id', 'host_dept_name', 'notes']:
        if _column_exists(conn, 'gov_meeting_arrangement', col):
            conn.execute(sa.text(f'ALTER TABLE gov_meeting_arrangement DROP COLUMN {col}'))

    for col in ['participant_dept_id', 'participant_dept_name', 'contact_phone', 'role_name']:
        if _column_exists(conn, 'gov_meeting_participant', col):
            conn.execute(sa.text(f'ALTER TABLE gov_meeting_participant DROP COLUMN {col}'))
