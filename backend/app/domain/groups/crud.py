import secrets
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.groups.model import Group, GroupMember


async def create_group(db: AsyncSession, name: str, admin_id: UUID, max_members: Optional[int] = None) -> Group:
    invite_code = secrets.token_urlsafe(16)
    group = Group(name=name, invite_code=invite_code, admin_id=admin_id, max_members=max_members)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    # הוסף את ה-admin כ-member
    member = GroupMember(group_id=group.group_id, user_id=admin_id, role="admin")
    db.add(member)
    await db.commit()
    return group


async def get_group_by_id(db: AsyncSession, group_id: UUID) -> Optional[Group]:
    result = await db.execute(select(Group).where(Group.group_id == group_id))
    return result.scalars().first()


async def get_group_by_invite_code(db: AsyncSession, invite_code: str) -> Optional[Group]:
    result = await db.execute(select(Group).where(Group.invite_code == invite_code))
    return result.scalars().first()


async def get_user_groups(db: AsyncSession, user_id: UUID) -> list[Group]:
    result = await db.execute(
        select(Group)
        .join(GroupMember, Group.group_id == GroupMember.group_id)
        .where(GroupMember.user_id == user_id, Group.is_active == True)
    )
    return list(result.scalars().all())


async def get_group_members(db: AsyncSession, group_id: UUID) -> list[GroupMember]:
    result = await db.execute(select(GroupMember).where(GroupMember.group_id == group_id))
    return list(result.scalars().all())


async def get_membership(db: AsyncSession, group_id: UUID, user_id: UUID) -> Optional[GroupMember]:
    result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    )
    return result.scalars().first()


async def join_group(db: AsyncSession, group_id: UUID, user_id: UUID) -> GroupMember:
    member = GroupMember(group_id=group_id, user_id=user_id, role="member")
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


async def remove_member(db: AsyncSession, group_id: UUID, user_id: UUID) -> None:
    member = await get_membership(db, group_id, user_id)
    if member:
        db.delete(member)
        await db.commit()


async def update_member_role(db: AsyncSession, group_id: UUID, user_id: UUID, role: str) -> Optional[GroupMember]:
    member = await get_membership(db, group_id, user_id)
    if member:
        member.role = role
        await db.commit()
        await db.refresh(member)
    return member


async def rename_group(db: AsyncSession, group: Group, name: str) -> Group:
    group.name = name
    await db.commit()
    await db.refresh(group)
    return group


async def close_group(db: AsyncSession, group: Group) -> Group:
    group.is_active = False
    await db.commit()
    return group


async def get_member_count(db: AsyncSession, group_id: UUID) -> int:
    result = await db.execute(
        select(func.count()).select_from(GroupMember).where(GroupMember.group_id == group_id)
    )
    return result.scalar_one()
