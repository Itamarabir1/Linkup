"""add refresh_token to users

Revision ID: add_refresh_token
Revises: add_route_summary
Create Date: 2026-02-03

Adds refresh_token (TEXT) to users table for JWT refresh tokens.
"""
from alembic import op
import sqlalchemy as sa

revision = "add_refresh_token"
down_revision = "add_route_summary"
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
    if not _column_exists(conn, "users", "refresh_token"):
        op.add_column(
            "users",
            sa.Column("refresh_token", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _column_exists(conn, "users", "refresh_token"):
        op.drop_column("users", "refresh_token")
