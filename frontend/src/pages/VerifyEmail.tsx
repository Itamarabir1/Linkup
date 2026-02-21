import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { api } from '../api/client';
import './Auth.css';

export default function VerifyEmail() {
  const location = useLocation();
  const navigate = useNavigate();
  const emailFromState = (location.state as { email?: string } | null)?.email;
  const emailFromQuery = new URLSearchParams(location.search).get('email');
  const email = emailFromState ?? emailFromQuery ?? '';

  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  if (!email) {
    return (
      <div className="auth-page">
        <h1 className="auth-title">אימות חשבון מייל</h1>
        <p className="auth-error">לא נמצא אימייל לאימות. נא להירשם או להיכנס מחדש.</p>
        <p className="auth-link">
          <Link to="/register">הרשמה</Link> · <Link to="/login">התחברות</Link>
        </p>
      </div>
    );
  }

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setError('נא להזין את הקוד שנשלח למייל');
      return;
    }
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      await api.post('/auth/verify-email', { code: code.trim(), email });
      setSuccess('החשבון אומת בהצלחה.');
      setTimeout(() => {
        navigate('/login', { replace: true, state: { email, verified: true } });
      }, 1200);
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, unknown> } })?.response;
      const data = res?.data ?? {};
      const raw = (data.message ?? data.detail) as string | unknown[] | undefined;
      let msg = (err as Error)?.message ?? 'אימות נכשל';
      if (raw !== undefined) {
        if (typeof raw === 'string') msg = raw;
        else if (Array.isArray(raw) && raw.length > 0) {
          const first = raw[0];
          msg =
            typeof first === 'object' && first !== null && 'msg' in first
              ? String((first as { msg: string }).msg)
              : JSON.stringify(raw);
        } else msg = JSON.stringify(raw);
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setSuccess('');
    setResendLoading(true);
    try {
      await api.post('/auth/resend-verification', { email });
      setSuccess('קוד חדש נשלח למייל.');
    } catch (err: unknown) {
      const res = (err as { response?: { data?: Record<string, unknown> } })?.response;
      const data = res?.data ?? {};
      const raw = (data.message ?? data.detail) as string | undefined;
      setError(typeof raw === 'string' ? raw : (err as Error)?.message ?? 'שליחת קוד מחדש נכשלה');
    } finally {
      setResendLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <h1 className="auth-title">אימות חשבון מייל</h1>
      <p style={{ marginBottom: '1rem', color: '#374151' }}>
        נשלח קוד אימות ל־<strong>{email}</strong>. הזן את הקוד למטה.
      </p>
      <form onSubmit={handleVerify} className="auth-form">
        {error && <p className="auth-error">{error}</p>}
        {success && <p style={{ color: '#059669', margin: 0 }}>{success}</p>}
        <input
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="קוד אימות (6 ספרות)"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
          className="auth-input"
          maxLength={6}
        />
        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? 'מאמת...' : 'אמת חשבון'}
        </button>
      </form>
      <p className="auth-link" style={{ marginTop: '1rem' }}>
        <button
          type="button"
          onClick={handleResend}
          disabled={resendLoading}
          style={{
            background: 'none',
            border: 'none',
            color: '#2563eb',
            cursor: resendLoading ? 'not-allowed' : 'pointer',
            padding: 0,
            fontSize: 'inherit',
          }}
        >
          {resendLoading ? 'שולח...' : 'שלח קוד שוב'}
        </button>
      </p>
      <p className="auth-link">
        <Link to="/login">חזרה להתחברות</Link>
      </p>
    </div>
  );
}
