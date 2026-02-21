import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import GoogleSignIn from '../components/GoogleSignIn';
import GoogleSignInDebug from '../components/GoogleSignInDebug';
import './Auth.css';

export default function Login() {
  const location = useLocation();
  const state = location.state as { email?: string; verified?: boolean } | null;
  const [email, setEmail] = useState(state?.email ?? '');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [verifiedMessage] = useState(Boolean(state?.verified));
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password) {
      setError('נא למלא אימייל וסיסמה');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const ax = err as { code?: string; message?: string; response?: { data?: Record<string, unknown> } };
      if (ax.code === 'ECONNABORTED' || (ax.message && ax.message.includes('timeout'))) {
        setError('השרת לא מגיב בזמן. וודא שהבקאנד רץ (למשל http://127.0.0.1:8000) ושה-URL ב-frontend/.env (VITE_API_URL) נכון.');
        return;
      }
      const res = ax?.response;
      const data = res?.data ?? {};
      const raw = (data.message ?? data.detail) as string | unknown[] | undefined;
      let msg = (err as Error)?.message ?? 'התחברות נכשלה';
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
    <div className="auth-page">
      <GoogleSignInDebug />
      <h1 className="auth-title">התחברות</h1>
      {verifiedMessage && (
        <p style={{ color: '#059669', marginBottom: '1rem' }}>החשבון אומת. התחבר כעת.</p>
      )}
      <form onSubmit={handleLogin} className="auth-form">
        {error && <p className="auth-error">{error}</p>}
        <input
          type="email"
          placeholder="אימייל"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="auth-input"
          autoComplete="email"
        />
        <input
          type="password"
          placeholder="סיסמה"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="auth-input"
          autoComplete="current-password"
        />
        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? 'מתחבר...' : 'התחבר'}
        </button>
      </form>
      
      <div style={{ margin: '1.5rem 0', textAlign: 'center', position: 'relative' }}>
        <div style={{
          position: 'absolute',
          top: '50%',
          left: 0,
          right: 0,
          height: '1px',
          backgroundColor: '#e5e7eb',
        }} />
        <span style={{
          position: 'relative',
          backgroundColor: '#fff',
          padding: '0 1rem',
          color: '#6b7280',
          fontSize: '0.875rem',
        }}>
          או
        </span>
      </div>

      <GoogleSignIn onError={setError} disabled={loading} />

      <p className="auth-link">
        <Link to="/register">אין חשבון? הירשם</Link>
      </p>
    </div>
  );
}
