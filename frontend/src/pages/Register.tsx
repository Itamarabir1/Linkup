import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import type { RegisterData } from '../context/AuthContext';
import { API_BASE_URL } from '../config/env';
import styles from './Register.module.css';

export default function Register() {
  const [form, setForm] = useState<RegisterData>({
    full_name: '',
    email: '',
    phone_number: '',
    password: '',
    confirm_password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [connectionTest, setConnectionTest] = useState<string | null>(null);
  const { register } = useAuth();
  const navigate = useNavigate();

  const testConnection = async () => {
    setConnectionTest('בודק...');
    try {
      const base = API_BASE_URL.replace(/\/api\/v1\/?$/, '');
      const res = await fetch(base + '/api/v1/health', { method: 'GET' });
      const data = await res.json().catch(() => ({}));
      setConnectionTest(res.ok ? `✓ חיבור OK: ${JSON.stringify(data)}` : `שגיאה ${res.status}`);
    } catch (e) {
      setConnectionTest('✗ לא הגיע לבקאנד: ' + (e instanceof Error ? e.message : String(e)));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (
      !form.full_name.trim() ||
      !form.email.trim() ||
      !form.phone_number.trim() ||
      !form.password ||
      !form.confirm_password
    ) {
      setError('נא למלא את כל השדות');
      return;
    }
    if (form.password !== form.confirm_password) {
      setError('הסיסמאות אינן תואמות');
      return;
    }
    if (form.password.length < 8) {
      setError('הסיסמה: לפחות 8 תווים, אות גדולה, אות קטנה, מספר ותו מיוחד (@$!%*?&)');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await register({ ...form, full_name: form.full_name.trim(), email: form.email.trim(), phone_number: form.phone_number.trim() });
      navigate('/verify-email', { replace: true, state: { email: form.email.trim() } });
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, unknown>; status?: number } })?.response;
      const data = res?.data ?? {};
      // Backend LinkupError uses "message"; FastAPI validation uses "detail"
      const raw = (data.message ?? data.detail) as string | unknown[] | undefined;
      let msg = (err as Error)?.message || 'הרשמה נכשלה';
      if (raw !== undefined) {
        if (typeof raw === 'string') msg = raw;
        else if (Array.isArray(raw) && raw.length > 0) {
          const first = raw[0];
          msg = typeof first === 'object' && first !== null && 'msg' in first
            ? String((first as { msg: string }).msg)
            : JSON.stringify(raw);
        } else msg = JSON.stringify(raw);
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.title}>הרשמה</h1>
      <form onSubmit={handleSubmit} className={styles.form}>
        {error && <p className={styles.error}>{error}</p>}
        <input
          type="text"
          placeholder="שם מלא"
          value={form.full_name}
          onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))}
          className={styles.input}
        />
        <input
          type="email"
          placeholder="אימייל"
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          className={styles.input}
          autoComplete="email"
        />
        <input
          type="tel"
          placeholder="טלפון (למשל 0501234567 או +972501234567)"
          value={form.phone_number}
          onChange={(e) =>
            setForm((f) => ({ ...f, phone_number: e.target.value }))
          }
          className={styles.input}
        />
        <input
          type="password"
          placeholder="סיסמה: 8+ תווים, A-Z, a-z, 0-9, תו מיוחד (@$!%*?&)"
          value={form.password}
          onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
          className={styles.input}
          autoComplete="new-password"
        />
        <input
          type="password"
          placeholder="אימות סיסמה"
          value={form.confirm_password}
          onChange={(e) =>
            setForm((f) => ({ ...f, confirm_password: e.target.value }))
          }
          className={styles.input}
          autoComplete="new-password"
        />
        <button type="submit" className={styles.button} disabled={loading}>
          {loading ? 'נרשם...' : 'הירשם'}
        </button>
      </form>
      <p className={styles.link}>
        <Link to="/login">כבר יש חשבון? התחבר</Link>
      </p>
      <p style={{ fontSize: 11, color: '#888', marginTop: 24, direction: 'ltr', textAlign: 'center' }}>
        API: {API_BASE_URL}
      </p>
      <p style={{ marginTop: 8, textAlign: 'center' }}>
        <button type="button" onClick={testConnection} style={{ fontSize: 12, padding: '6px 12px' }}>
          בדיקת חיבור לבקאנד
        </button>
        {connectionTest && (
          <span style={{ display: 'block', marginTop: 8, fontSize: 12, color: connectionTest.startsWith('✓') ? '#059669' : '#dc2626' }}>
            {connectionTest}
          </span>
        )}
      </p>
    </div>
  );
}
