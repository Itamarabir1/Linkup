"""add distance_km and duration_min to rides

Revision ID: add_ride_km_time
Revises:
Create Date: 2025-02-03

Adds distance_km (Numeric) and duration_min (Numeric) to rides table if missing.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "add_ride_km_time"
down_revision = None
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
    if not _column_exists(conn, "rides", "distance_km"):
        op.add_column(
            "rides",
            sa.Column("distance_km", sa.Numeric(10, 2), nullable=True),
        )
    if not _column_exists(conn, "rides", "duration_min"):
        op.add_column(
            "rides",
            sa.Column("duration_min", sa.Numeric(10, 2), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "rides", "duration_min"):
        op.drop_column("rides", "duration_min")
    if _column_exists(conn, "rides", "distance_km"):
        op.drop_column("rides", "distance_km")
