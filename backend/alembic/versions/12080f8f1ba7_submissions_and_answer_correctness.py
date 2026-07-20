"""submissions and answer correctness

Revision ID: 12080f8f1ba7
Revises: ce04705e34e7
Create Date: 2026-07-20 05:10:12.282424

"""

from collections.abc import Sequence

from alembic import op

revision: str = "12080f8f1ba7"
down_revision: str | Sequence[str] | None = "ce04705e34e7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE answers ADD COLUMN is_correct boolean")

    op.execute("""
      CREATE TABLE submissions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        attempt_id uuid NOT NULL UNIQUE REFERENCES attempts(id),
        correct_count int NOT NULL DEFAULT 0,
        total_count int NOT NULL DEFAULT 0,
        score numeric(5, 2) NOT NULL DEFAULT 0,
        graded_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("ALTER TABLE submissions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE submissions FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON submissions "
        "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
        "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON submissions TO app_user")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS submissions CASCADE")
    op.execute("ALTER TABLE answers DROP COLUMN IF EXISTS is_correct")
