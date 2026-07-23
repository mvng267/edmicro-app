"""support tickets and comments

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-21 05:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
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
      CREATE TABLE tickets (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        subject text NOT NULL,
        body text NOT NULL DEFAULT '',
        status text NOT NULL DEFAULT 'open',
        created_by uuid NOT NULL,
        assigned_to uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_tickets_tenant ON tickets (tenant_id, status, created_at)")
    _rls("tickets")

    op.execute("""
      CREATE TABLE ticket_comments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        ticket_id uuid NOT NULL REFERENCES tickets(id),
        author_id uuid NOT NULL,
        body text NOT NULL,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_ticket_comments ON ticket_comments (tenant_id, ticket_id)")
    _rls("ticket_comments")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS ticket_comments CASCADE")
    op.execute("DROP TABLE IF EXISTS tickets CASCADE")
