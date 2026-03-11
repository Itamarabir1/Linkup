import { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getGroupMembers,
  removeMember,
  promoteMember,
  leaveGroup,
  closeGroup,
  renameGroup,
} from '../api/groups';
import { useAuth } from '../context/AuthContext';
import { useGroup } from '../context/GroupContext';
import type { GroupMember as GroupMemberType } from '../types/api';
import styles from './GroupManage.module.css';

export default function GroupManage() {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { myGroups, isLoadingGroups, refreshGroups } = useGroup();
  const [members, setMembers] = useState<GroupMemberType[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [error, setError] = useState('');
  const [editingName, setEditingName] = useState(false);
  const [editNameValue, setEditNameValue] = useState('');
  const [savingName, setSavingName] = useState(false);
  const [copyInviteDone, setCopyInviteDone] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [confirmClose, setConfirmClose] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);

  const group = groupId ? (myGroups.find((g) => g.group_id === groupId) ?? null) : null;

  const loadMembers = useCallback(async () => {
    if (!groupId) return;
    setLoadingMembers(true);
    setError('');
    try {
      const list = await getGroupMembers(groupId);
      setMembers(list);
    } catch {
      setError('טעינת חברי הקבוצה נכשלה');
      setMembers([]);
    } finally {
      setLoadingMembers(false);
    }
  }, [groupId]);

  useEffect(() => {
    refreshGroups();
  }, [refreshGroups]);

  useEffect(() => {
    loadMembers();
  }, [loadMembers]);

  useEffect(() => {
    if (group && !editingName) setEditNameValue(group.name);
  }, [group?.name, editingName]);

  if (!groupId) {
    return (
      <div className={styles.page}>
        <p className={styles.pageError}>חסר מזהה קבוצה.</p>
      </div>
    );
  }

  if (!isLoadingGroups && !group) {
    return (
      <div className={styles.page}>
        <p className={styles.pageError}>הקבוצה לא נמצאה או שאין לך גישה אליה.</p>
      </div>
    );
  }

  if (!group) {
    return (
      <div className={styles.page}>
        <div className={styles.pageLoading}>טוען...</div>
      </div>
    );
  }

  const isAdmin = group.admin_id === user?.user_id;
  const inviteUrl = typeof window !== 'undefined' ? `${window.location.origin}/join/${group.invite_code}` : '';

  const handleCopyInvite = () => {
    if (!inviteUrl) return;
    navigator.clipboard.writeText(inviteUrl).then(() => {
      setCopyInviteDone(true);
      setTimeout(() => setCopyInviteDone(false), 2000);
    });
  };

  const handleSaveName = async () => {
    const trimmed = editNameValue.trim();
    if (!trimmed || trimmed === group.name) {
      setEditingName(false);
      return;
    }
    setSavingName(true);
    setError('');
    try {
      await renameGroup(groupId, trimmed);
      await refreshGroups();
      setEditingName(false);
    } catch {
      setError('שינוי השם נכשל');
    } finally {
      setSavingName(false);
    }
  };

  const handleRemoveMember = async (userId: string) => {
    setActionLoading(true);
    setError('');
    try {
      await removeMember(groupId, userId);
      await loadMembers();
      await refreshGroups();
    } catch {
      setError('הסרת החבר נכשלה');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePromoteMember = async (userId: string) => {
    setActionLoading(true);
    setError('');
    try {
      await promoteMember(groupId, userId);
      await loadMembers();
      await refreshGroups();
    } catch {
      setError('העלאת החבר למנהל נכשלה');
    } finally {
      setActionLoading(false);
    }
  };

  const handleLeave = async () => {
    setActionLoading(true);
    setError('');
    try {
      await leaveGroup(groupId);
      setConfirmLeave(false);
      await refreshGroups();
      navigate('/', { replace: true });
    } catch {
      setError('עזיבת הקבוצה נכשלה');
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    setActionLoading(true);
    setError('');
    try {
      await closeGroup(groupId);
      setConfirmClose(false);
      await refreshGroups();
      navigate('/', { replace: true });
    } catch {
      setError('סגירת הקבוצה נכשלה');
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <div className={styles.groupNameWrap}>
        {editingName ? (
          <>
            <input
              type="text"
              className={styles.groupNameInput}
              value={editNameValue}
              onChange={(e) => setEditNameValue(e.target.value)}
              onBlur={handleSaveName}
              onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
              disabled={savingName}
              autoFocus
            />
            {savingName && <span>שומר...</span>}
          </>
        ) : (
          <button
            type="button"
            className={styles.pageTitle}
            style={{ border: 'none', background: 'none', cursor: isAdmin ? 'pointer' : 'default', padding: 0 }}
            onClick={() => isAdmin && setEditingName(true)}
          >
            {group.name}
          </button>
        )}
      </div>

      {error && <p className={styles.pageError}>{error}</p>}

      <section className={styles.inviteSection}>
        <div className={styles.inviteLabel}>קישור הזמנה</div>
        <div className={styles.inviteRow}>
          <input type="text" className={styles.inviteInput} value={inviteUrl} readOnly />
          <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCopyInvite}>
            העתק
          </button>
          {copyInviteDone && <span className={styles.copiedToast}>הועתק!</span>}
        </div>
      </section>

      <h2 className={styles.membersTitle}>חברי הקבוצה</h2>
      {loadingMembers ? (
        <div className={styles.pageLoading}>טוען חברים...</div>
      ) : (
        <div className={styles.memberList}>
          {members.length === 0 ? (
            <p className={styles.emptyText}>אין חברים בקבוצה.</p>
          ) : (
            members.map((m) => {
              const isCurrentUser = m.user_id === user?.user_id;
              const canRemove = isAdmin && !isCurrentUser && m.role !== 'admin';
              const canPromote = isAdmin && m.role === 'member';
              return (
                <div key={m.id} className={styles.memberRow}>
                  <div className={styles.memberInfo}>
                    <span className={styles.memberName}>{m.full_name ?? m.user_id}</span>
                    <span className={`${styles.roleBadge} ${m.role === 'admin' ? styles.roleBadgeAdmin : ''}`}>
                      {m.role === 'admin' ? 'מנהל' : 'חבר'}
                    </span>
                  </div>
                  <div className={styles.memberActions}>
                    {canPromote && (
                      <button
                        type="button"
                        className={`${styles.btn} ${styles.btnOutline}`}
                        onClick={() => handlePromoteMember(m.user_id)}
                        disabled={actionLoading}
                      >
                        הפוך למנהל
                      </button>
                    )}
                    {canRemove && (
                      <button
                        type="button"
                        className={`${styles.btn} ${styles.btnDanger}`}
                        onClick={() => handleRemoveMember(m.user_id)}
                        disabled={actionLoading}
                      >
                        הסר
                      </button>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      <div className={styles.actionsSection}>
        {!isAdmin && (
          <button
            type="button"
            className={`${styles.btn} ${styles.btnDanger}`}
            onClick={() => setConfirmLeave(true)}
            disabled={actionLoading}
          >
            עזוב קבוצה
          </button>
        )}
        {isAdmin && (
          <button
            type="button"
            className={`${styles.btn} ${styles.btnDanger}`}
            onClick={() => setConfirmClose(true)}
            disabled={actionLoading}
          >
            סגור קבוצה
          </button>
        )}
      </div>

      {confirmLeave && (
        <div
          className={styles.confirmModalBackdrop}
          role="dialog"
          aria-modal="true"
          onClick={() => !actionLoading && setConfirmLeave(false)}
        >
          <div className={styles.confirmModalBox} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.confirmModalTitle}>לעזוב את הקבוצה?</h2>
            <div className={styles.confirmModalActions}>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnOutline}`}
                onClick={() => setConfirmLeave(false)}
                disabled={actionLoading}
              >
                ביטול
              </button>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnDanger}`}
                onClick={handleLeave}
                disabled={actionLoading}
              >
                {actionLoading ? '...' : 'עזוב'}
              </button>
            </div>
          </div>
        </div>
      )}

      {confirmClose && (
        <div
          className={styles.confirmModalBackdrop}
          role="dialog"
          aria-modal="true"
          onClick={() => !actionLoading && setConfirmClose(false)}
        >
          <div className={styles.confirmModalBox} onClick={(e) => e.stopPropagation()}>
            <h2 className={styles.confirmModalTitle}>לסגור את הקבוצה?</h2>
            <p style={{ color: '#6b7280', marginTop: 0 }}>חברים לא יוכלו יותר להצטרף. ניתן יהיה לפתוח מחדש בעתיד.</p>
            <div className={styles.confirmModalActions}>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnOutline}`}
                onClick={() => setConfirmClose(false)}
                disabled={actionLoading}
              >
                ביטול
              </button>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnDanger}`}
                onClick={handleClose}
                disabled={actionLoading}
              >
                {actionLoading ? '...' : 'סגור קבוצה'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
