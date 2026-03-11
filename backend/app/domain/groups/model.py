"""
Groups domain – SQLAlchemy models.
Group: named group with invite code and admin.
GroupMember: user membership in a group (role: admin or member).
"""

import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base


class Group(Base):
    __tablename__ = "groups"

    group_id = Column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name = Column(String(255), nullable=False)
    invite_code = Column(String(64), unique=True, nullable=False)
    admin_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active = Column(Boolean, default=True, server_default="true")
    max_members = Column(Integer, nullable=True)
    invite_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admin = relationship("User", back_populates="owned_groups")
    members = relationship(
        "GroupMember",
        back_populates="group",
        cascade="all, delete-orphan",
    )


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    group_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("groups.group_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(20), nullable=False, server_default="member")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
    )
