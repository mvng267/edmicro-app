"""org tables branches classes users scopes import

Revision ID: 055a7fc2306a
Revises: 8649dfa4ed68
Create Date: 2026-07-17 14:21:37.093603

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

revision: str = "055a7fc2306a"
down_revision: Union[str, Sequence[str], None] = "8649dfa4ed68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Bảng nghiệp vụ tenant: bật RLS + policy tenant_isolation + grant app_user
_RLS_TABLES = [
    "branches",
    "classes",
    "class_staff",
    "class_students",
    "user_scopes",
    "parent_students",
    "consents",
    "import_jobs",
    "import_rows",
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
    # users: thêm dob + parent_phone
    op.execute("ALTER TABLE users ADD COLUMN dob date")
    op.execute("ALTER TABLE users ADD COLUMN parent_phone text")

    # Server default cho cột vận hành (app/seed/test khỏi phải ghi tường minh)
    op.execute("ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active'")
    op.execute("ALTER TABLE users ALTER COLUMN full_name SET DEFAULT ''")
    op.execute("ALTER TABLE users ALTER COLUMN must_change_password SET DEFAULT true")
    op.execute("ALTER TABLE tenants ALTER COLUMN status SET DEFAULT 'active'")
    op.execute("ALTER TABLE tenants ALTER COLUMN settings SET DEFAULT '{}'::jsonb")

    op.execute("""
      CREATE TABLE branches (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        name text NOT NULL,
        address text,
        status text NOT NULL DEFAULT 'active',
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)

    op.execute("""
      CREATE TABLE classes (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        branch_id uuid NOT NULL REFERENCES branches(id),
        name text NOT NULL,
        language text NOT NULL DEFAULT 'en',
        level text,
        capacity int,
        start_date date,
        end_date date,
        status text NOT NULL DEFAULT 'active',
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_classes_branch ON classes (tenant_id, branch_id)")

    op.execute("""
      CREATE TABLE class_staff (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        class_id uuid NOT NULL REFERENCES classes(id),
        user_id uuid NOT NULL,
        role text NOT NULL,
        UNIQUE (class_id, user_id)
      )
    """)

    op.execute("""
      CREATE TABLE class_students (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        class_id uuid NOT NULL REFERENCES classes(id),
        user_id uuid NOT NULL,
        joined_at timestamptz NOT NULL DEFAULT now(),
        left_at timestamptz
      )
    """)
    op.execute(
        "CREATE UNIQUE INDEX uq_class_student_active ON class_students (class_id, user_id) "
        "WHERE left_at IS NULL"
    )

    op.execute("""
      CREATE TABLE user_scopes (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        user_id uuid NOT NULL,
        branch_id uuid,
        language text
      )
    """)
    op.execute("CREATE INDEX ix_user_scopes_user ON user_scopes (tenant_id, user_id)")

    op.execute("""
      CREATE TABLE parent_students (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        parent_user_id uuid NOT NULL,
        student_user_id uuid NOT NULL,
        linked_by uuid,
        created_at timestamptz NOT NULL DEFAULT now(),
        UNIQUE (parent_user_id, student_user_id)
      )
    """)

    op.execute("""
      CREATE TABLE consents (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        user_id uuid NOT NULL UNIQUE,
        status text NOT NULL DEFAULT 'pending',
        note text,
        updated_by uuid,
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)

    op.execute("""
      CREATE TABLE import_jobs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        filename text,
        status text NOT NULL DEFAULT 'validated',
        summary jsonb,
        created_by uuid,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)

    op.execute("""
      CREATE TABLE import_rows (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        job_id uuid NOT NULL REFERENCES import_jobs(id),
        row_no int NOT NULL,
        data jsonb NOT NULL,
        error text,
        action text NOT NULL DEFAULT 'create'
      )
    """)
    op.execute("CREATE INDEX ix_import_rows_job ON import_rows (job_id)")

    for t in _RLS_TABLES:
        _enable_rls(t)


def downgrade() -> None:
    for t in reversed(_RLS_TABLES):
        op.execute(f"DROP TABLE IF EXISTS {t} CASCADE")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS dob")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS parent_phone")
