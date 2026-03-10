import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { listConversations } from '../api/client';
import type { ConversationListItem } from '../api/client';
import { formatDateTimeNoSeconds } from '../utils/date';
import styles from './Messages.module.css';

export default function Messages() {
  const { user } = useAuth();
  const [list, setList] = useState<ConversationListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchList = useCallback(async () => {
    if (!user?.user_id) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await listConversations();
      const sorted = (Array.isArray(data) ? data : []).slice().sort((a, b) => {
        const at = a.last_message_at ? new Date(a.last_message_at).getTime() : 0;
        const bt = b.last_message_at ? new Date(b.last_message_at).getTime() : 0;
        return bt - at;
      });
      setList(sorted);
    } catch {
      setError('לא ניתן לטעון את השיחות');
    } finally {
      setLoading(false);
    }
  }, [user?.user_id]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  if (loading) {
    return (
      <div className={styles.page}>
        <h1 className={styles.pageTitle}>הודעות</h1>
        <p className={styles.pageLoading}>טוען...</p>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>הודעות</h1>
      <p className={styles.pageMeta} style={{ color: '#6b7280', marginBottom: '1rem' }}>
        שיחות עם נהגים ונוסעים (רק עם מי שיש ביניכם קשר נסיעה).
      </p>
      {error && <p className={styles.pageError}>{error}</p>}
      <div className={styles.cardList}>
        {list.length === 0 ? (
          <p className={styles.emptyText}>אין שיחות. פתח שיחה מההתראות, מההזמנות או מנסיעות כנהג.</p>
        ) : (
          list.map((c) => (
            <Link
              key={c.conversation_id}
              to={`/messages/${c.conversation_id}`}
              className={styles.card}
              style={{
                display: 'block',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              <div className={styles.cardRoute} style={{ fontWeight: 600 }}>
                {c.partner.full_name || `משתמש #${c.partner.user_id}`}
              </div>
              {c.last_message_preview && (
                <div className={styles.cardMeta} style={{ marginTop: '0.25rem', color: '#6b7280' }}>
                  {c.last_message_preview}
                </div>
              )}
              {c.last_message_at && (
                <div className={styles.cardMeta} style={{ marginTop: '0.25rem', fontSize: '0.85em' }}>
                  {formatDateTimeNoSeconds(c.last_message_at)}
                </div>
              )}
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
