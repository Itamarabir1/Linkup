"""Rename users.avatar_url to users.avatar_key (S3 key prefix only).

Revision ID: 002_avatar_key
Revises: 001_full_schema
Create Date: 2025-03-09

DB is empty; no data migration. Run: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa


revision = "002_avatar_key"
down_revision = "001_full_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "avatar_url",
        new_column_name="avatar_key",
        existing_type=sa.String(500),
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "avatar_key",
        new_column_name="avatar_url",
        existing_type=sa.String(500),
    )
