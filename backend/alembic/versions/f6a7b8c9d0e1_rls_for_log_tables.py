"""bật RLS cho activity_logs + audit_logs (bịt lỗ đọc chéo tenant)

Trước đó 2 bảng log không bật RLS (tenant_id nullable) nên mọi query phải nhớ lọc
tenant tường minh — quên là lộ log tenant khác. Bật RLS FORCE + policy để DB tự chặn.
Log ở tầng app luôn ghi kèm tenant_id thật (mọi call log_activity/log_audit đều truyền
current.tenant_id), nên WITH CHECK không phá luồng ghi. Bảng vẫn append-only:
app_user chỉ có INSERT + SELECT.

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-21 06:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | Sequence[str] | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES = ("activity_logs", "audit_logs")


def upgrade() -> None:
    for t in _TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY tenant_isolation ON {t} "
            "USING (tenant_id = current_setting('app.tenant_id', true)::uuid) "
            "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)"
        )


def downgrade() -> None:
    for t in _TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t}")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY")
