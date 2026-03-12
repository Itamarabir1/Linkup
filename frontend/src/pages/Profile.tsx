import { useRef, useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import { compressImage } from '../utils/imageUtils';
import styles from './Profile.module.css';

const ACCEPT_AVATAR = 'image/jpeg,image/png,image/webp';
const MAX_SIZE_MB = 5;

export default function Profile() {
  const { user, logout, refreshUser } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const prevAvatarUrlRef = useRef<string | null | undefined>(null);
  const avatarCacheBusterRef = useRef<number>(0);
  const [uploading, setUploading] = useState(false);
  const [removing, setRemoving] = useState(false);
  const [error, setError] = useState('');
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
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
    if (avatarPreview) URL.revokeObjectURL(avatarPreview);
    setAvatarPreview(URL.createObjectURL(file));
    try {
      const compressed = await compressImage(file, { maxWidth: 800, quality: 0.85 });
      const { data: uploadData } = await api.get<{ upload_url: string; staging_key: string }>(
        '/users/me/avatar/upload-url'
      );
      await fetch(uploadData.upload_url, {
        method: 'PUT',
        body: compressed,
        headers: { 'Content-Type': 'image/webp' },
      });
      await api.post('/users/me/avatar/confirm', { staging_key: uploadData.staging_key });
      await refreshUser();
      if (avatarPreview) URL.revokeObjectURL(avatarPreview);
      setAvatarPreview(null);
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, unknown> } })?.response;
      const data = res?.data ?? {};
      const raw = (data.message ?? data.detail) as string | undefined;
      setError(typeof raw === 'string' ? raw : (err as Error)?.message ?? 'העלאת תמונה נכשלה');
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveAvatar = async () => {
    if (!user?.avatar_key && !(user as { avatar_url?: string })?.avatar_url) return;
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

  const profileAvatarUrl = (user as { avatar_url_medium?: string; avatar_url?: string })?.avatar_url_medium
    ?? (user as { avatar_url?: string })?.avatar_url;
  const hasValidAvatar = (profileAvatarUrl || avatarPreview) && !avatarLoadError;
  const avatarSrc = avatarPreview
    ? avatarPreview
    : profileAvatarUrl
      ? `${encodeURI(profileAvatarUrl)}${profileAvatarUrl.includes('?') ? '&' : '?'}_v=${avatarCacheBusterRef.current}`
      : '';

  useEffect(() => {
    const currentUrl = profileAvatarUrl ?? null;
    if (prevAvatarUrlRef.current !== currentUrl) {
      prevAvatarUrlRef.current = currentUrl;
      avatarCacheBusterRef.current = Date.now();
      setAvatarLoadError(false);
    }
  }, [profileAvatarUrl]);

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

      {avatarExpanded && hasValidAvatar && avatarSrc && (
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
