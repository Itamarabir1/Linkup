import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { PassengerRequest } from '../types/api';
import { formatDateTimeNoSeconds } from '../utils/date';
import './AppPages.css';

const statusLabels: Record<string, string> = {
  active: 'מחפש נסיעות',
  pending: 'ממתין לאישור',
  approved: 'אושר',
  rejected: 'נדחה',
  completed: 'הושלם',
  expired: 'פג תוקף',
  matched: 'התאמה נמצאה',
  cancelled: 'בוטל',
};

export default function MyRequests() {
  const [requests, setRequests] = useState<PassengerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [requestToCancel, setRequestToCancel] = useState<PassengerRequest | null>(null);
  const [cancelling, setCancelling] = useState(false);

  const fetchRequests = useCallback(async () => {
    try {
      const { data } = await api.get<PassengerRequest[]>(
        '/passenger/passengers/me'
      );
      const all = Array.isArray(data) ? data : [];
      // לא להציג בקשות שבוטלו במסך
      setRequests(all.filter((r) => r.status !== 'cancelled'));
      setError('');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'טעינת בקשות נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  if (loading) {
    return (
      <div className="page">
        <div className="page-loading">טוען...</div>
      </div>
    );
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h1 className="page-title" style={{ margin: 0 }}>בקשות הטרמפ שלי</h1>
        <Link to="/search" className="btn btn-success">
          🔍 חפש טרמפ
        </Link>
      </div>
      {error && <p className="page-error">{error}</p>}
      <div className="card-list">
        {requests.length === 0 ? (
          <p className="empty-text">אין בקשות. חפש נסיעות ושמור בקשה.</p>
        ) : (
          requests.map((r) => (
            <div key={r.request_id} className="card card-request card-ride-wrap">
              {r.status !== 'cancelled' && (
                <button
                  type="button"
                  className="card-ride-delete-btn"
                  onClick={() => setRequestToCancel(r)}
                  disabled={cancelling}
                  aria-label="הסר בקשת טרמפ"
                  title="הסר בקשה"
                >
                  ✕
                </button>
              )}
              <div className="card-route">
                {r.pickup_name ?? '?'} ← {r.destination_name ?? '?'}
              </div>
              <div className="card-meta">
                {formatDateTimeNoSeconds(r.requested_departure_time)} ·{' '}
                סטטוס: {statusLabels[r.status] || r.status}
              </div>
            </div>
          ))
        )}
      </div>

      {requestToCancel && (
        <div
          className="confirm-modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-cancel-request-title"
          onClick={() => (!cancelling ? setRequestToCancel(null) : null)}
        >
          <div
            className="confirm-modal-box"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="confirm-cancel-request-title" className="confirm-modal-title">
              האם אתה בטוח שאתה רוצה להסיר את בקשת הטרמפ הזו?
            </h2>
            <p style={{ color: '#6b7280', marginTop: 0 }}>
              זה יבטל גם בקשות הצטרפות שנשלחו לנהגים (אם קיימות).
            </p>
            <div className="confirm-modal-actions">
              <button
                type="button"
                className="btn btn-outline"
                onClick={() => setRequestToCancel(null)}
                disabled={cancelling}
              >
                ביטול
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={async () => {
                  if (!requestToCancel) return;
                  setCancelling(true);
                  setError('');
                  try {
                    await api.delete(`/passenger/passengers/${requestToCancel.request_id}/cancel`);
                    // להסיר מהרשימה אחרי ביטול
                    setRequests((prev) =>
                      prev.filter((p) => p.request_id !== requestToCancel.request_id)
                    );
                    setRequestToCancel(null);
                  } catch (err: unknown) {
                    const msg =
                      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
                      'ביטול הבקשה נכשל';
                    setError(typeof msg === 'string' ? msg : String(msg));
                  } finally {
                    setCancelling(false);
                  }
                }}
                disabled={cancelling}
              >
                {cancelling ? 'מבטל...' : 'אישור'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
