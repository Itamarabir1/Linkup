"""add route_summary to rides

Revision ID: add_route_summary
Revises: add_ride_km_time
Create Date: 2025-02-03

Adds route_summary (VARCHAR 255) to rides table if missing.
"""
from alembic import op
import sqlalchemy as sa

revision = "add_route_summary"
down_revision = "add_ride_km_time"
branch_labels = None
depends_on = None


def _column_exists(connection, table: str, column: str) -> bool:
    r = connection.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    )
    return r.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    if not _column_exists(conn, "rides", "route_summary"):
        op.add_column(
            "rides",
            sa.Column("route_summary", sa.String(255), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "rides", "route_summary"):
        op.drop_column("rides", "route_summary")
