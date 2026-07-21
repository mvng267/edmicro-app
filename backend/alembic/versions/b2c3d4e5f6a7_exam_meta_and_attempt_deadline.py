"""exam meta and attempt deadline

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-20 08:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # đề thi = practice + exam_meta (thời lượng + bảng quy đổi band). content_id = practices.id
    op.execute("""
      CREATE TABLE exam_meta (
        content_id uuid PRIMARY KEY REFERENCES practices(id),
        tenant_id uuid NOT NULL,
        duration_minutes int NOT NULL,
        band_scale jsonb NOT NULL DEFAULT '[]'::jsonb,
        review_allowed boolean NOT NULL DEFAULT true,
        created_at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute("ALTER TABLE exam_meta ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE exam_meta FORCE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY tenant_isolation ON exam_meta "
        "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
        "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
    )
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON exam_meta TO app_user")

    # đồng hồ server: hạn nộp cố định lúc bắt đầu (null với practice)
    op.execute("ALTER TABLE attempts ADD COLUMN deadline_at timestamptz")


def downgrade() -> None:
    op.execute("ALTER TABLE attempts DROP COLUMN IF EXISTS deadline_at")
    op.execute("DROP TABLE IF EXISTS exam_meta CASCADE")
