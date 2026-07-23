"""courses, lessons, progress and gamification

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-21 03:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
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
      CREATE TABLE courses (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        name text NOT NULL,
        language text NOT NULL DEFAULT 'en',
        status text NOT NULL DEFAULT 'draft',
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    _rls("courses")

    op.execute("""
      CREATE TABLE lessons (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        course_id uuid NOT NULL REFERENCES courses(id),
        sort_order int NOT NULL DEFAULT 0,
        title text NOT NULL,
        kind text NOT NULL DEFAULT 'text',
        body text NOT NULL DEFAULT '',
        content_ref uuid,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_lessons_course ON lessons (tenant_id, course_id, sort_order)")
    _rls("lessons")

    op.execute("""
      CREATE TABLE course_classes (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        course_id uuid NOT NULL REFERENCES courses(id),
        class_id uuid NOT NULL REFERENCES classes(id),
        assigned_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (course_id, class_id)
      )
    """)
    _rls("course_classes")

    op.execute("""
      CREATE TABLE lesson_progress (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        student_id uuid NOT NULL,
        lesson_id uuid NOT NULL REFERENCES lessons(id),
        completed_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (student_id, lesson_id)
      )
    """)
    _rls("lesson_progress")

    op.execute("""
      CREATE TABLE points_ledger (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        student_id uuid NOT NULL,
        points int NOT NULL,
        reason text NOT NULL,
        ref_type text,
        ref_id uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (student_id, reason, ref_id)
      )
    """)
    op.execute("CREATE INDEX ix_points_student ON points_ledger (tenant_id, student_id)")
    _rls("points_ledger")

    op.execute("""
      CREATE TABLE student_badges (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        student_id uuid NOT NULL,
        badge_code text NOT NULL,
        earned_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (student_id, badge_code)
      )
    """)
    _rls("student_badges")


def downgrade() -> None:
    for t in (
        "student_badges",
        "points_ledger",
        "lesson_progress",
        "course_classes",
        "lessons",
        "courses",
    ):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
