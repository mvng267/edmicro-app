"""activity and audit logs

Revision ID: 8649dfa4ed68
Revises: e422c968d257
Create Date: 2026-07-17 13:58:25.606149

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8649dfa4ed68'
down_revision: Union[str, Sequence[str], None] = 'e422c968d257'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
      CREATE TABLE activity_logs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid,
        actor_id uuid, actor_role text,
        action text NOT NULL, module text NOT NULL,
        entity_type text, entity_id uuid, entity_label text,
        diff jsonb, request_id text, ip text, user_agent text,
        at timestamptz NOT NULL DEFAULT now()
      )
    """)
    op.execute(
        "CREATE INDEX ix_activity_tenant_entity "
        "ON activity_logs (tenant_id, entity_type, entity_id, at)"
    )
    op.execute(
        "CREATE INDEX ix_activity_tenant_actor ON activity_logs (tenant_id, actor_id, at)"
    )
    op.execute("""
      CREATE TABLE audit_logs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        tenant_id uuid, actor_id uuid, actor_role text,
        action text NOT NULL, target_type text, target_id uuid,
        before jsonb, after jsonb, ip text, user_agent text,
        at timestamptz NOT NULL DEFAULT now()
      )
    """)
    # append-only: app_user chỉ INSERT + SELECT, không UPDATE/DELETE
    op.execute("REVOKE ALL ON activity_logs, audit_logs FROM app_user")
    op.execute("GRANT INSERT, SELECT ON activity_logs, audit_logs TO app_user")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS activity_logs")
    op.execute("DROP TABLE IF EXISTS audit_logs")
