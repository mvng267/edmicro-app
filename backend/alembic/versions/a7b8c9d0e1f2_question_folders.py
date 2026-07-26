"""question folders (cây thư mục kho câu hỏi)

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-07-26 22:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: str | Sequence[str] | None = "f6a7b8c9d0e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
      CREATE TABLE question_folders (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        parent_id uuid REFERENCES question_folders(id),
        name text NOT NULL,
        sort_order int NOT NULL DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_qfolders_parent ON question_folders (tenant_id, parent_id)")
    op.execute("ALTER TABLE question_folders ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE question_folders FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON question_folders "
        "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
        "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON question_folders TO app_user")

    op.execute("ALTER TABLE questions ADD COLUMN folder_id uuid REFERENCES question_folders(id)")
    op.execute("CREATE INDEX ix_questions_folder ON questions (tenant_id, folder_id)")


def downgrade() -> None:
    op.execute("ALTER TABLE questions DROP COLUMN IF EXISTS folder_id")
    op.execute("DROP TABLE IF EXISTS question_folders CASCADE")
