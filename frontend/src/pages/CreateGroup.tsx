import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createGroup } from '../api/groups';
import styles from './CreateGroup.module.css';

export default function CreateGroup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [createdGroup, setCreatedGroup] = useState<{ inviteCode: string; name: string } | null>(null);

  useEffect(() => {
    if (!createdGroup) return;
    const t = setTimeout(() => navigate('/', { replace: true }), 3000);
    return () => clearTimeout(t);
  }, [createdGroup, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = name.trim();
    if (!trimmed) return;
    setSubmitting(true);
    setError('');
    try {
      const group = await createGroup(trimmed);
      setCreatedGroup({ inviteCode: group.invite_code, name: group.name });
    } catch {
      setError('יצירת הקבוצה נכשלה.');
    } finally {
      setSubmitting(false);
    }
  };

  const inviteUrl =
    createdGroup && typeof window !== 'undefined'
      ? `${window.location.origin}/join/${createdGroup.inviteCode}`
      : '';

  const handleCopy = () => {
    if (!inviteUrl) return;
    navigator.clipboard.writeText(inviteUrl);
  };

  if (createdGroup) {
    return (
      <div className={styles.page}>
        <h1 className={styles.pageTitle}>הקבוצה נוצרה</h1>
        <div className={styles.successSection}>
          <div className={styles.successTitle}>הזמן חברים עם הקישור:</div>
          <div className={styles.inviteRow}>
            <input type="text" className={styles.inviteInput} value={inviteUrl} readOnly />
            <button type="button" className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleCopy}>
              העתק
            </button>
          </div>
          <p className={styles.redirectNote}>מעביר לדף הבית בעוד 3 שניות...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>צור קבוצה</h1>
      {error && <p className={styles.pageError}>{error}</p>}
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.label} htmlFor="group-name">
          שם הקבוצה
        </label>
        <input
          id="group-name"
          type="text"
          className={styles.input}
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="למשל: נסיעות לתל אביב"
          required
        />
        <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={submitting}>
          {submitting ? 'יוצר...' : 'צור קבוצה'}
        </button>
      </form>
    </div>
  );
}
