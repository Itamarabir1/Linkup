"""Add groups.avatar_key and groups.description.

Revision ID: 003_groups_avatar_desc
Revises: 002_avatar_key
Create Date: 2025-03-09

Run: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa


revision = "003_groups_avatar_desc"
down_revision = "002_avatar_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'groups' AND column_name = 'avatar_key') THEN
                ALTER TABLE groups ADD COLUMN avatar_key VARCHAR(255);
            END IF;
        END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'groups' AND column_name = 'description') THEN
                ALTER TABLE groups ADD COLUMN description VARCHAR(500);
            END IF;
        END $$
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("ALTER TABLE groups DROP COLUMN IF EXISTS description"))
    conn.execute(sa.text("ALTER TABLE groups DROP COLUMN IF EXISTS avatar_key"))
