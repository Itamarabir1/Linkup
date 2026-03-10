import { useRef, useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import styles from './Profile.module.css';

const ACCEPT_AVATAR = 'image/jpeg,image/png,image/webp';
const MAX_SIZE_MB = 5;

export default function Profile() {
  const { user, logout, refreshUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState('');
  const [avatarExpanded, setAvatarExpanded] = useState(false);
  const [avatarLoadError, setAvatarLoadError] = useState(false);

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`גודל מקסימלי ${MAX_SIZE_MB}MB`);
      return;
    }
    const ok = ['image/jpeg', 'image/png', 'image/webp'].includes(file.type);
    if (!ok) {
      setError('סוג קובץ: JPEG, PNG או WebP בלבד');
      return;
    }
    setError('');
    setAvatarLoadError(false);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      await api.post('/users/me/avatar', formData);
      
      // Polling עד שהתמונה מוכנה (ה-worker מעדכן את avatar_url)
      // מנסים עד 6 פעמים עם הפסקות של 0.8 שניות (סה"כ עד ~5 שניות)
      let attempts = 0;
      const maxAttempts = 6;
      const pollInterval = 800;
      
      const pollForAvatar = async (): Promise<void> => {
        await refreshUser();
        attempts++;
        
        // בודקים אם יש avatar_url חדש (משתמש ב-state המעודכן)
        // נשתמש ב-useEffect כדי לבדוק את השינוי
        if (attempts >= maxAttempts) {
          setUploading(false);
          // לא מציגים שגיאה - התמונה כנראה תגיע בקרוב
          return;
        }
        
        // ממשיך לנסות
        setTimeout(pollForAvatar, pollInterval);
      };
      
      // מתחיל polling מיד ואז כל 0.8 שניות
      await refreshUser(); // רענון ראשון מיד
      setTimeout(pollForAvatar, pollInterval);
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, unknown> } })?.response;
      const data = res?.data ?? {};
      const raw = (data.message ?? data.detail) as string | undefined;
      setError(typeof raw === 'string' ? raw : (err as Error)?.message ?? 'העלאת תמונה נכשלה');
      setUploading(false);
    }
  };

  const handleRemoveAvatar = async () => {
    setError('');
    setRemoving(true);
    setAvatarLoadError(false);
    try {
      await api.delete('/users/me/avatar');
      await refreshUser();
      setTimeout(() => refreshUser(), 2000);
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, unknown> } })?.response;
      const raw = (res?.data?.message ?? res?.data?.detail) as string | undefined;
      setError(typeof raw === 'string' ? raw : (err as Error)?.message ?? 'הסרת תמונה נכשלה');
    } finally {
      setRemoving(false);
    }
  };

  const handleAvatarImageError = () => {
    // אם התמונה לא נטענת, מתייחסים כאילו אין avatar_url
    setAvatarLoadError(true);
  };

  // אם יש avatar_url אבל התמונה לא נטענה, מתייחסים כאילו אין avatar_url
  const hasValidAvatar = user?.avatar_url && !avatarLoadError;
  const avatarSrc = user?.avatar_url ? encodeURI(user.avatar_url) : '';

  // איפוס שגיאת טעינת תמונה כשהמשתמש או avatar_url משתנים
  useEffect(() => {
    setAvatarLoadError(false);
    // אם יש avatar_url חדש אחרי העלאה, מסיים את מצב ההעלאה
    if (user?.avatar_url && uploading) {
      setUploading(false);
    }
  }, [user?.avatar_url, uploading]);

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>פרופיל</h1>
      {error && <p className={styles.pageError} style={{ marginBottom: '1rem' }}>{error}</p>}
      {user && (
        <div className={`${styles.card} ${styles.profileCard}`}>
          <div className={styles.profileAvatarBlock}>
            <div
              className={hasValidAvatar ? `${styles.profileAvatarWrap} ${styles.profileAvatarClickable}` : styles.profileAvatarWrap}
              onClick={() => hasValidAvatar && setAvatarExpanded(true)}
              role={hasValidAvatar ? 'button' : undefined}
              aria-label={hasValidAvatar ? 'הצג תמונה בהגדלה' : undefined}
            >
              {hasValidAvatar ? (
                <img 
                  src={avatarSrc} 
                  alt="" 
                  className={styles.profileAvatarImg}
                  onError={handleAvatarImageError}
                />
              ) : (
                <div className={styles.profileAvatarPlaceholder}>
                  {(user.full_name || user.email || '?').charAt(0).toUpperCase()}
                </div>
              )}
              {uploading && <div className={styles.profileAvatarOverlay}>מתעדכן...</div>}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPT_AVATAR}
              onChange={handleAvatarChange}
              style={{ display: 'none' }}
              disabled={uploading}
            />
            <div className={styles.profileAvatarLinks}>
              {hasValidAvatar ? (
                <>
                  <button
                    type="button"
                    className={styles.profileAvatarLink}
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading || removing}
                  >
                    {uploading ? 'מעלה...' : 'החלף תמונה'}
                  </button>
                  <span className={styles.profileAvatarLinkSep}>·</span>
                  <button
                    type="button"
                    className={`${styles.profileAvatarLink} ${styles.profileAvatarLinkMuted}`}
                    onClick={handleRemoveAvatar}
                    disabled={uploading || removing}
                  >
                    {removing ? 'מסיר...' : 'הסר תמונה'}
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  className={styles.profileAvatarLink}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  {uploading ? 'מעלה...' : 'העלאת תמונה'}
                </button>
              )}
            </div>
          </div>

      <div className={styles.profileRow}>
            <span className={styles.profileLabel}>שם</span>
            <span className={styles.profileValue}>
              {user.full_name || user.first_name || user.email}
            </span>
          </div>
          <div className={styles.profileRow}>
            <span className={styles.profileLabel}>אימייל</span>
            <span className={styles.profileValue}>{user.email}</span>
          </div>
          {user.phone_number && (
            <div className={styles.profileRow}>
              <span className={styles.profileLabel}>טלפון</span>
              <span className={styles.profileValue}>{user.phone_number}</span>
            </div>
          )}
        </div>
      )}

      {avatarExpanded && hasValidAvatar && user?.avatar_url && (
        <div
          className={styles.avatarModalBackdrop}
          onClick={() => setAvatarExpanded(false)}
          onKeyDown={(e) => e.key === 'Escape' && setAvatarExpanded(false)}
          role="button"
          tabIndex={0}
          aria-label="סגור"
        >
          <button
            type="button"
            className={styles.avatarModalClose}
            onClick={() => setAvatarExpanded(false)}
            aria-label="סגור"
          >
            ×
          </button>
          <img
            src={avatarSrc}
            alt="תמונת פרופיל"
            className={styles.avatarModalImg}
            onClick={(e) => e.stopPropagation()}
            onError={() => {
              setAvatarExpanded(false);
              handleAvatarImageError();
            }}
          />
        </div>
      )}

      <button type="button" className={`${styles.btn} ${styles.btnDanger}`} onClick={() => logout()}>
        התנתק
      </button>
    </div>
  );
}
