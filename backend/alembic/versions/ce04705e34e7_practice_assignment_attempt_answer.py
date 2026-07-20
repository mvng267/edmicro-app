"""practice assignment attempt answer

Revision ID: ce04705e34e7
Revises: 87d2d5a583d0
Create Date: 2026-07-20 02:11:45.746851

"""

from collections.abc import Sequence

from alembic import op

revision: str = "ce04705e34e7"
down_revision: str | Sequence[str] | None = "87d2d5a583d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RLS = [
    "practices",
    "practice_questions",
    "assignments",
    "assignment_assignees",
    "attempts",
    "answers",
]


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
      CREATE TABLE practices (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        name text NOT NULL,
        skill text,
        language text NOT NULL DEFAULT 'en',
        level text,
        settings jsonb NOT NULL DEFAULT '{}'::jsonb,
        status text NOT NULL DEFAULT 'published',
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)

    op.execute("""
      CREATE TABLE practice_questions (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        practice_id uuid NOT NULL REFERENCES practices(id),
        question_version_id uuid NOT NULL,
        sort_order int NOT NULL,
        UNIQUE (practice_id, sort_order)
      )
    """)

    op.execute("""
      CREATE TABLE assignments (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        content_kind text NOT NULL DEFAULT 'practice',
        content_id uuid NOT NULL,
        class_id uuid NOT NULL,
        available_from timestamptz,
        due_at timestamptz,
        late_policy text NOT NULL DEFAULT 'allow_late',
        status text NOT NULL DEFAULT 'active',
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_assignments_class ON assignments (tenant_id, class_id)")

    op.execute("""
      CREATE TABLE assignment_assignees (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        assignment_id uuid NOT NULL REFERENCES assignments(id),
        student_id uuid NOT NULL,
        derived_status text NOT NULL DEFAULT 'not_opened',
        submitted_at timestamptz,
        is_late boolean NOT NULL DEFAULT false,
        UNIQUE (assignment_id, student_id)
      )
    """)
    op.execute("CREATE INDEX ix_assignees_student ON assignment_assignees (tenant_id, student_id)")

    op.execute("""
      CREATE TABLE attempts (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        assignee_id uuid NOT NULL REFERENCES assignment_assignees(id),
        kind text NOT NULL DEFAULT 'practice',
        status text NOT NULL DEFAULT 'in_progress',
        started_at timestamptz NOT NULL DEFAULT now(),
        submitted_at timestamptz
      )
    """)

    op.execute("""
      CREATE TABLE answers (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        attempt_id uuid NOT NULL REFERENCES attempts(id),
        question_version_id uuid NOT NULL,
        payload jsonb,
        saved_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (attempt_id, question_version_id)
      )
    """)

    for t in _RLS:
        _enable_rls(t)


def downgrade() -> None:
    for t in reversed(_RLS):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
