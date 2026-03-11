"""Pydantic schemas for Groups domain."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    max_members: Optional[int] = None
    invite_expires_at: Optional[datetime] = None


class GroupOut(BaseModel):
    group_id: UUID
    name: str
    invite_code: str
    admin_id: UUID
    is_active: bool
    max_members: Optional[int] = None
    invite_expires_at: Optional[datetime] = None
    created_at: datetime


class GroupMemberOut(BaseModel):
    id: UUID
    group_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime
