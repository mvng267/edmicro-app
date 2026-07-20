"""content questions and versions

Revision ID: 87d2d5a583d0
Revises: 055a7fc2306a
Create Date: 2026-07-20 01:39:10.467172

"""

from collections.abc import Sequence

from alembic import op

revision: str = "87d2d5a583d0"
down_revision: str | Sequence[str] | None = "055a7fc2306a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS = ["questions", "question_versions"]


def _enable_rls(table: str) -> None:
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
      CREATE TABLE questions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        is_global boolean NOT NULL DEFAULT false,
        type text NOT NULL,
        language text NOT NULL DEFAULT 'en',
        skill text,
        level text,
        exam_tag text,
        topic text,
        difficulty int,
        status text NOT NULL DEFAULT 'draft',
        current_version_id uuid,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute(
        "CREATE INDEX ix_questions_filter ON questions (tenant_id, language, skill, level, status)"
    )

    op.execute("""
      CREATE TABLE question_versions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        question_id uuid NOT NULL REFERENCES questions(id),
        version_no int NOT NULL,
        content jsonb NOT NULL,
        answer_key jsonb,
        explanation text,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (question_id, version_no)
      )
    """)

    for t in _RLS:
        _enable_rls(t)


def downgrade() -> None:
    for t in reversed(_RLS):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
