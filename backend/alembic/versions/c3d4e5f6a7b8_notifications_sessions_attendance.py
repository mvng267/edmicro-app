"""notifications, class sessions and attendance

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-21 02:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rls(table: str) -> None:
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON {table} "
        "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
        "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_user")


def upgrade() -> None:
    op.execute("""
      CREATE TABLE notifications (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        user_id uuid NOT NULL,
        event_code text NOT NULL,
        title text NOT NULL,
        body text NOT NULL DEFAULT '',
        entity_type text,
        entity_id uuid,
        channel text NOT NULL DEFAULT 'in_app',
        read_at timestamptz,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_notifications_user ON notifications (tenant_id, user_id, read_at)")
    _rls("notifications")

    op.execute("""
      CREATE TABLE class_sessions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        class_id uuid NOT NULL REFERENCES classes(id),
        starts_at timestamptz NOT NULL,
        ends_at timestamptz NOT NULL,
        topic text NOT NULL DEFAULT '',
        online_link text,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_sessions_class ON class_sessions (tenant_id, class_id, starts_at)")
    _rls("class_sessions")

    op.execute("""
      CREATE TABLE attendance (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        session_id uuid NOT NULL REFERENCES class_sessions(id),
        student_id uuid NOT NULL,
        status text NOT NULL DEFAULT 'present',
        note text,
        marked_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (session_id, student_id)
      )
    """)
    _rls("attendance")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS attendance CASCADE")
    op.execute("DROP TABLE IF EXISTS class_sessions CASCADE")
    op.execute("DROP TABLE IF EXISTS notifications CASCADE")
