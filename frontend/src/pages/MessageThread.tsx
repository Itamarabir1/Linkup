import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getConversation,
  getMessages,
  sendMessage,
  type ConversationDetail,
  type MessageResponse,
} from '../api/client';
import { formatDateTimeNoSeconds } from '../utils/date';
import styles from './MessageThread.module.css';

export default function MessageThread() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { user } = useAuth();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const cid = conversationId ? parseInt(conversationId, 10) : NaN;

  const fetchConversation = useCallback(async () => {
    if (!cid || !user?.user_id) return;
    setLoading(true);
    setError('');
    try {
      const [convRes, msgRes] = await Promise.all([
        getConversation(cid),
        getMessages(cid, { limit: 100 }),
      ]);
      setConversation(convRes.data);
      setMessages(Array.isArray(msgRes.data) ? msgRes.data : []);
    } catch {
      setError('לא ניתן לטעון את השיחה');
    } finally {
      setLoading(false);
    }
  }, [cid, user?.user_id]);

  useEffect(() => {
    fetchConversation();
  }, [fetchConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = input.trim();
    if (!body || !cid || sending) return;
    setSending(true);
    setError('');
    try {
      const { data } = await sendMessage(cid, body);
      setMessages((prev) => [...prev, data]);
      setInput('');
    } catch {
      setError('שליחת ההודעה נכשלה');
    } finally {
      setSending(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <p className="page-loading">טוען שיחה...</p>
      </div>
    );
  }

  if (error && !conversation) {
    return (
      <div className={styles.page}>
        <p className={styles.pageError}>{error}</p>
        <Link to="/messages" className={`${styles.btn} ${styles.btnOutline}`} style={{ marginTop: '1rem' }}>
          חזרה להודעות
        </Link>
      </div>
    );
  }

  const partnerName = conversation?.partner?.full_name || `שיחה #${cid}`;

  return (
    <div className={styles.page} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Link to="/messages" className={`${styles.btn} ${styles.btnOutline}`} style={{ fontSize: '0.875rem' }}>
          ← הודעות
        </Link>
        <h1 className={styles.pageTitle} style={{ margin: 0, flex: 1 }}>
          {partnerName}
        </h1>
      </div>
      {error && <p className={styles.pageError}>{error}</p>}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          border: '1px solid #e5e7eb',
          borderRadius: 8,
          padding: '1rem',
          minHeight: 200,
          maxHeight: 400,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}
      >
        {messages.length === 0 ? (
          <p className={styles.emptyText} style={{ margin: 'auto' }}>
            אין הודעות. שלח הודעה ראשונה.
          </p>
        ) : (
          messages.map((m) => {
            const isMe = m.sender_id === user?.user_id;
            return (
              <div
                key={m.message_id}
                style={{
                  alignSelf: isMe ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: 8,
                  background: isMe ? 'var(--primary, #2563eb)' : 'var(--surface, #f3f4f6)',
                  color: isMe ? '#fff' : 'inherit',
                }}
              >
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{m.body}</div>
                <div
                  style={{
                    fontSize: '0.75rem',
                    opacity: 0.85,
                    marginTop: '0.25rem',
                  }}
                >
                  {formatDateTimeNoSeconds(m.created_at)}
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="כתוב הודעה..."
          className={styles.formInput}
          style={{ flex: 1 }}
          maxLength={10000}
        />
        <button type="submit" className={`${styles.btn} ${styles.btnSuccess}`} disabled={sending || !input.trim()}>
          {sending ? '...' : 'שלח'}
        </button>
      </form>
    </div>
  );
}
