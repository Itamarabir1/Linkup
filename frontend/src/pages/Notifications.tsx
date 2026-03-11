import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, openChatByBooking } from '../api/client';
import type { NotificationItem } from '../types/api';
import { formatDateTimeNoSeconds } from '../utils/date';
import styles from './Notifications.module.css';

export default function Notifications() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [list, setList] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionBookingId, setActionBookingId] = useState<string | null>(null);
  const [chatLoading, setChatLoading] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  const fetchNotifications = useCallback(async () => {
    if (!user?.user_id) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await api.get<NotificationItem[]>('/users/me/notifications');
      setList(Array.isArray(data) ? data : []);
    } catch {
      setError('לא ניתן לטעון את ההתראות');
    } finally {
      setLoading(false);
    }
  }, [user?.user_id]);

  useEffect(() => {
    fetchNotifications();
  }, [fetchNotifications]);

  const handleApprove = async (bookingId: string) => {
    if (!user?.user_id) return;
    setActionBookingId(bookingId);
    setError('');
    try {
      await api.patch(`/bookings/${bookingId}/approve`, null, {
        params: { driver_id: user.user_id },
      });
      await fetchNotifications();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string; detail?: string } } })?.response?.data
          ?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'אישור הבקשה נכשל';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setActionBookingId(null);
    }
  };

  const handleReject = async (bookingId: string) => {
    if (!user?.user_id) return;
    setActionBookingId(bookingId);
    setError('');
    try {
      await api.patch(`/bookings/${bookingId}/reject`, null, {
        params: { driver_id: user.user_id },
      });
      await fetchNotifications();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string; detail?: string } } })?.response?.data
          ?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'דחיית הבקשה נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setActionBookingId(null);
    }
  };

  const handleOpenChat = async (bookingId: string) => {
    setChatLoading(bookingId);
    setError('');
    try {
      const conversation = await openChatByBooking(bookingId);
      navigate(`/messages/${conversation.conversation_id}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'פתיחת שיחה נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setChatLoading(null);
    }
  };

  // חישוב התראות חדשות (24 שעות) והתראות להצגה
  const now = new Date();
  const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
  const newNotifications = list.filter(n => new Date(n.created_at) >= yesterday);
  const displayedNotifications = showAll ? list : list.slice(0, 10);

  const isNewNotification = (notification: NotificationItem) => {
    return new Date(notification.created_at) >= yesterday;
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <h1 className={styles.pageTitle}>התראות</h1>
        <p className={styles.pageLoading}>טוען...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>התראות</h1>
      {newNotifications.length > 0 && (
        <p className={styles.pageMeta} style={{ color: '#2563eb', marginBottom: '1rem', fontWeight: 500 }}>
          יש לך {newNotifications.length} התראות חדשות
        </p>
      )}
      <p className={styles.pageMeta} style={{ color: '#6b7280', marginBottom: '1rem' }}>
        כל ההתראות שלך: בקשות להצטרפות (כנהג), אישור/דחייה (כנוסע).
      </p>
      {error && <p className={styles.pageError}>{error}</p>}
      <div className={styles.cardList}>
        {list.length === 0 ? (
          <p className={styles.emptyText}>אין התראות.</p>
        ) : (
          <>
            {displayedNotifications.map((n) => {
              const isNew = isNewNotification(n);
              return (
                <div 
                  key={`${n.booking_id}-${n.created_at}`} 
                  className={styles.card}
                  style={{
                    borderLeft: isNew ? '4px solid #2563eb' : undefined,
                    backgroundColor: isNew ? '#f0f9ff' : undefined,
                  }}
                >
                  {isNew && (
                    <div style={{ 
                      fontSize: '0.75rem', 
                      color: '#2563eb', 
                      fontWeight: 600, 
                      marginBottom: '0.5rem' 
                    }}>
                      חדש
                    </div>
                  )}
                  <div className={styles.cardRoute} style={{ fontWeight: 600 }}>
                    {n.title}
                  </div>
                  {n.body && (
                    <div className={styles.cardMeta} style={{ marginTop: '0.25rem' }}>
                      {n.body}
                    </div>
                  )}
                  {(n.ride_origin || n.ride_destination) && (
                    <div className={`${styles.cardMeta} ${styles.cardRouteSummary}`}>
                      {n.ride_origin ?? '?'} → {n.ride_destination ?? '?'}
                    </div>
                  )}
                  <div className={styles.cardMeta} style={{ marginTop: '0.25rem', fontSize: '0.9em', color: '#6b7280' }}>
                    {formatDateTimeNoSeconds(n.created_at)}
                  </div>
                  {n.type === 'ride_request' && (
                    <div className={styles.cardActions} style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        className={`${styles.btn} ${styles.btnSuccess}`}
                        onClick={() => handleApprove(n.booking_id)}
                        disabled={actionBookingId === n.booking_id}
                      >
                        {actionBookingId === n.booking_id ? '...' : 'אישור'}
                      </button>
                      <button
                        type="button"
                        className={`${styles.btn} ${styles.btnOutline}`}
                        onClick={() => handleReject(n.booking_id)}
                        disabled={actionBookingId === n.booking_id}
                      >
                        דחייה
                      </button>
                      <button
                        type="button"
                        className={`${styles.btn} ${styles.btnOutline}`}
                        onClick={() => handleOpenChat(n.booking_id)}
                        disabled={chatLoading === n.booking_id}
                      >
                        {chatLoading === n.booking_id ? '...' : 'שיחה'}
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
            {list.length > 10 && !showAll && (
              <button
                type="button"
                className={`${styles.btn} ${styles.btnOutline}`}
                onClick={() => setShowAll(true)}
                style={{ 
                  marginTop: '1rem', 
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '1rem'
                }}
              >
                הצג עוד ({list.length - 10} התראות נוספות)
              </button>
            )}
            {showAll && list.length > 10 && (
              <button
                type="button"
                className={`${styles.btn} ${styles.btnOutline}`}
                onClick={() => setShowAll(false)}
                style={{ 
                  marginTop: '1rem', 
                  width: '100%',
                  padding: '0.75rem',
                  fontSize: '1rem'
                }}
              >
                הצג פחות
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
}
