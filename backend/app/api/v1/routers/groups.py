from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, get_current_user
from app.domain.groups import crud, service
from app.domain.groups.schema import GroupCreate, GroupOut, GroupMemberOut
from app.domain.users.model import User

router = APIRouter()


@router.post("", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.create_group(db, data, current_user.user_id)


@router.get("/my", response_model=list[GroupOut])
async def get_my_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.get_my_groups(db, current_user.user_id)


@router.get("/join/{invite_code}", response_model=GroupOut)
async def get_group_by_invite(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await crud.get_group_by_invite_code(db, invite_code)
    if not group:
        raise HTTPException(status_code=404, detail="קבוצה לא נמצאה")
    count = await crud.get_member_count(db, group.group_id)
    return GroupOut.model_validate({**group.__dict__, "member_count": count})


@router.post("/join/{invite_code}", response_model=GroupOut)
async def join_group(
    invite_code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await service.join_by_invite(db, invite_code, current_user.user_id)


@router.get("/{group_id}/members", response_model=list[GroupMemberOut])
async def get_members(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = await crud.get_membership(db, group_id, current_user.user_id)
    if not membership:
        raise HTTPException(status_code=403, detail="אינך חבר בקבוצה")
    return await crud.get_group_members(db, group_id)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = await crud.get_membership(db, group_id, current_user.user_id)
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="רק אדמין יכול להסיר חברים")
    await crud.remove_member(db, group_id, user_id)


@router.patch("/{group_id}/members/{user_id}/promote", response_model=GroupMemberOut)
async def promote_member(
    group_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    membership = await crud.get_membership(db, group_id, current_user.user_id)
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="רק אדמין יכול לקדם חברים")
    return await crud.update_member_role(db, group_id, user_id, "admin")


@router.delete("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await crud.remove_member(db, group_id, current_user.user_id)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await crud.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="קבוצה לא נמצאה")
    if group.admin_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="רק אדמין יכול לסגור קבוצה")
    await crud.close_group(db, group)


@router.patch("/{group_id}/rename", response_model=GroupOut)
async def rename_group(
    group_id: UUID,
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    group = await crud.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="קבוצה לא נמצאה")
    if group.admin_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="רק אדמין יכול לשנות שם")
    updated = await crud.rename_group(db, group, name)
    count = await crud.get_member_count(db, group_id)
    return GroupOut.model_validate({**updated.__dict__, "member_count": count})
