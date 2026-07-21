"""ai grading queue, quota and open-answer scores

Revision ID: a1b2c3d4e5f6
Revises: 12080f8f1ba7
Create Date: 2026-07-20 07:40:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "12080f8f1ba7"
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
    # điểm chấm mở (writing) trên từng answer; câu đóng để null các cột này
    op.execute("ALTER TABLE answers ADD COLUMN ai_score numeric(4, 3)")
    op.execute("ALTER TABLE answers ADD COLUMN ai_feedback text")
    op.execute("ALTER TABLE answers ADD COLUMN ai_confidence numeric(4, 3)")
    op.execute("ALTER TABLE answers ADD COLUMN final_score numeric(4, 3)")
    # grade_status: null (câu đóng) | pending | ai_graded | needs_manual | finalized
    op.execute("ALTER TABLE answers ADD COLUMN grade_status text")

    # submission: final (mọi câu đã chốt) | provisional (còn câu mở chờ GV)
    op.execute("ALTER TABLE submissions ADD COLUMN status text NOT NULL DEFAULT 'final'")

    # hàng đợi chấm AI: 1 job / 1 câu mở
    op.execute("""
      CREATE TABLE grading_jobs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        attempt_id uuid NOT NULL REFERENCES attempts(id),
        answer_id uuid NOT NULL UNIQUE REFERENCES answers(id),
        status text NOT NULL DEFAULT 'pending',
        priority int NOT NULL DEFAULT 0,
        created_at timestamptz NOT NULL DEFAULT now(),
        updated_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("CREATE INDEX ix_grading_jobs_status ON grading_jobs (tenant_id, status)")
    _rls("grading_jobs")

    # hạn mức chấm AI theo tenant + kỳ (yyyy-mm)
    op.execute("""
      CREATE TABLE tenant_ai_quota (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid NOT NULL,
        period text NOT NULL,
        writing_limit int NOT NULL DEFAULT 0,
        writing_used int NOT NULL DEFAULT 0,
        UNIQUE (tenant_id, period)
      )
    """)
    _rls("tenant_ai_quota")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenant_ai_quota CASCADE")
    op.execute("DROP TABLE IF EXISTS grading_jobs CASCADE")
    op.execute("ALTER TABLE submissions DROP COLUMN IF EXISTS status")
    for col in ("ai_score", "ai_feedback", "ai_confidence", "final_score", "grade_status"):
        op.execute(f"ALTER TABLE answers DROP COLUMN IF EXISTS {col}")
