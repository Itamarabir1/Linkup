"""add groups feature

Revision ID: 003_add_groups
Revises: 002_google_id
Create Date: 2025-03-09

Creates groups and group_members tables, adds group_id to rides and passenger_requests.
"""
from alembic import op
import sqlalchemy as sa


revision = "003_add_groups"
down_revision = "002_google_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create groups table
    op.create_table(
        "groups",
        sa.Column("group_id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("invite_code", sa.String(64), nullable=False),
        sa.Column("admin_id", sa.UUID(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("max_members", sa.Integer(), nullable=True),
        sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["admin_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("group_id"),
    )
    op.create_index("ix_groups_invite_code", "groups", ["invite_code"], unique=True)

    # 2. Create group_members table
    op.create_table(
        "group_members",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(20), server_default="member", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.group_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )

    # 3. Add group_id to rides
    op.add_column(
        "rides",
        sa.Column("group_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_rides_group_id",
        "rides",
        "groups",
        ["group_id"],
        ["group_id"],
        ondelete="SET NULL",
    )

    # 4. Add group_id to passenger_requests
    op.add_column(
        "passenger_requests",
        sa.Column("group_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_passenger_requests_group_id",
        "passenger_requests",
        "groups",
        ["group_id"],
        ["group_id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # 1. Drop group_id from passenger_requests
    op.drop_constraint("fk_passenger_requests_group_id", "passenger_requests", type_="foreignkey")
    op.drop_column("passenger_requests", "group_id")

    # 2. Drop group_id from rides
    op.drop_constraint("fk_rides_group_id", "rides", type_="foreignkey")
    op.drop_column("rides", "group_id")

    # 3. Drop group_members table
    op.drop_table("group_members")

    # 4. Drop groups table
    op.drop_index("ix_groups_invite_code", table_name="groups")
    op.drop_table("groups")
