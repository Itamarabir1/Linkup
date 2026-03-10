"""normalize ride_status enum

Revision ID: normalize_ride_status
Revises: add_refresh_token
Create Date: 2026-02-03

Normalize ride_status to lowercase values: open, full, completed, cancelled.
Maps legacy 'OPEN' and 'in_progress' to 'open'.
"""
from alembic import op

revision = "normalize_ride_status"
down_revision = "add_refresh_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE ride_status_new AS ENUM ('open', 'full', 'completed', 'cancelled')")
    op.execute("ALTER TABLE rides ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE rides ALTER COLUMN status TYPE ride_status_new "
        "USING (CASE status::text WHEN 'OPEN' THEN 'open'::ride_status_new "
        "WHEN 'in_progress' THEN 'open'::ride_status_new ELSE status::text::ride_status_new END)"
    )
    op.execute("ALTER TABLE rides ALTER COLUMN status SET DEFAULT 'open'::ride_status_new")
    op.execute("DROP TYPE ride_status")
    op.execute("ALTER TYPE ride_status_new RENAME TO ride_status")


def downgrade() -> None:
    # Recreate type with same normalized values so schema remains valid
    op.execute("CREATE TYPE ride_status_old AS ENUM ('open', 'full', 'completed', 'cancelled')")
    op.execute("ALTER TABLE rides ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE rides ALTER COLUMN status TYPE ride_status_old USING status::text::ride_status_old"
    )
    op.execute("ALTER TABLE rides ALTER COLUMN status SET DEFAULT 'open'::ride_status_old")
    op.execute("DROP TYPE ride_status")
    op.execute("ALTER TYPE ride_status_old RENAME TO ride_status")
