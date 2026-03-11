import { api } from './client';
import type { Group, GroupMember } from '../types/api';

// יצירת קבוצה חדשה
export async function createGroup(name: string): Promise<Group> {
  const { data } = await api.post<Group>('/groups', { name });
  return data;
}

// שליפת הקבוצות שלי
export async function getMyGroups(): Promise<Group[]> {
  const { data } = await api.get<Group[]>('/groups/my');
  return data;
}

// שליפת קבוצה לפי invite_code (לדף הצטרפות)
export async function getGroupByInviteCode(inviteCode: string): Promise<Group> {
  const { data } = await api.get<Group>(`/groups/join/${inviteCode}`);
  return data;
}

// הצטרפות לקבוצה
export async function joinGroup(inviteCode: string): Promise<void> {
  await api.post(`/groups/join/${inviteCode}`);
}

// שליפת חברי קבוצה
export async function getGroupMembers(groupId: string): Promise<GroupMember[]> {
  const { data } = await api.get<GroupMember[]>(`/groups/${groupId}/members`);
  return data;
}

// הסרת חבר (מנהל בלבד)
export async function removeMember(groupId: string, userId: string): Promise<void> {
  await api.delete(`/groups/${groupId}/members/${userId}`);
}

// העלאת חבר למנהל
export async function promoteMember(groupId: string, userId: string): Promise<void> {
  await api.patch(`/groups/${groupId}/members/${userId}/promote`);
}

// עזיבת קבוצה
export async function leaveGroup(groupId: string): Promise<void> {
  await api.post(`/groups/${groupId}/leave`);
}

// סגירת קבוצה (מנהל בלבד)
export async function closeGroup(groupId: string): Promise<void> {
  await api.patch(`/groups/${groupId}/close`);
}

// שינוי שם קבוצה (מנהל בלבד)
export async function renameGroup(groupId: string, name: string): Promise<Group> {
  const { data } = await api.patch<Group>(`/groups/${groupId}`, { name });
  return data;
}
