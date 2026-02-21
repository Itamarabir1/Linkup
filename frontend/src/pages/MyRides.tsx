import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Ride } from '../types/api';
import { formatDateTimeNoSeconds } from '../utils/date';
import { API_BASE_URL } from '../config/env';
import { useAuth } from '../context/AuthContext';
import './AppPages.css';

function getRideWsUrl(rideId: number): string {
  const base = API_BASE_URL.startsWith('http')
    ? API_BASE_URL.replace(/^http/, 'ws')
    : (typeof window !== 'undefined'
        ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}${API_BASE_URL}`
        : `${API_BASE_URL}`);
  return `${base}/rides/ws/${rideId}`;
}

export default function MyRides() {
  const { user } = useAuth();
  const [rides, setRides] = useState<Ride[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [rideToCancel, setRideToCancel] = useState<number | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const wsRefs = useRef<Map<number, WebSocket>>(new Map());

  const fetchRides = useCallback(async () => {
    try {
      const { data } = await api.get<Ride[]>('/rides/me');
      const active = (Array.isArray(data) ? data : []).filter(
        (r) => r.status !== 'cancelled'
      );
      setRides(active);
      setError('');
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'טעינת נסיעות נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setLoading(false);
    }
  }, [user?.user_id]);

  useEffect(() => {
    fetchRides();
  }, [fetchRides]);

  // WebSocket: חיבור לערוץ של כל נסיעה כדי לקבל RIDE_CANCELLED. סוגרים רק נסיעות שיצאו מהרשימה (לא את כולם) כדי לא לסגור חיבורים לפני שהתבססו.
  useEffect(() => {
    const rideIds = rides.map((r) => r.ride_id);
    const currentIds = new Set(rideIds);

    rideIds.forEach((rideId) => {
      if (wsRefs.current.has(rideId)) return;
      const url = getRideWsUrl(rideId);
      let ws: WebSocket;
      try {
        ws = new WebSocket(url);
        wsRefs.current.set(rideId, ws);
        ws.onmessage = (ev) => {
          try {
            const payload = JSON.parse(ev.data as string) as { event?: string };
            if (payload.event === 'RIDE_CANCELLED') {
              setRides((prev) => prev.filter((r) => r.ride_id !== rideId));
            }
          } catch {
            // לא JSON או פורמט אחר – מתעלמים
          }
        };
        ws.onclose = () => {
          wsRefs.current.delete(rideId);
        };
      } catch {
        wsRefs.current.delete(rideId);
      }
    });

    wsRefs.current.forEach((sock, id) => {
      if (!currentIds.has(id)) {
        sock.close();
        wsRefs.current.delete(id);
      }
    });

    return () => {
      // סגירת כל החיבורים רק ב-unmount של הקומפוננטה (לא בכל שינוי rides)
    };
  }, [rides]);

  // ב-unmount: סגירת כל ה-WebSockets
  useEffect(() => {
    return () => {
      wsRefs.current.forEach((sock) => sock.close());
      wsRefs.current.clear();
    };
  }, []);

  const handleConfirmCancel = useCallback(async () => {
    if (rideToCancel == null) return;
    setCancelling(true);
    setError('');
    try {
      await api.delete(`/rides/${rideToCancel}/cancel`);
      setRides((prev) => prev.filter((r) => r.ride_id !== rideToCancel));
      setRideToCancel(null);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'ביטול הנסיעה נכשל';
      setError(typeof msg === 'string' ? msg : String(msg));
      setRideToCancel(null);
    } finally {
      setCancelling(false);
    }
  }, [rideToCancel]);

  if (loading) {
    return (
      <div className="page">
        <div className="page-loading">טוען...</div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <h1 className="page-title">הנסיעות שלי</h1>
        <Link to="/create-ride" className="btn btn-primary">
          + נסיעה חדשה
        </Link>
      </header>
      {error && <p className="page-error">{error}</p>}
      <div className="card-list">
        {rides.length === 0 ? (
          <p className="empty-text">אין נסיעות. צור נסיעה חדשה.</p>
        ) : (
          rides.map((r) => (
            <div key={r.ride_id} className="card card-ride card-ride-wrap">
              <button
                type="button"
                className="card-ride-delete-btn"
                onClick={() => setRideToCancel(r.ride_id)}
                title="מחק נסיעה"
                aria-label="מחק נסיעה"
              >
                ×
              </button>
              <div className="card-route">
                {r.origin_name ?? '?'} → {r.destination_name ?? '?'}
              </div>
              <div className="card-meta">
                {formatDateTimeNoSeconds(r.departure_time)} ·{' '}
                {r.available_seats} מושבים · {r.status}
              </div>
              {r.route_summary && (
                <div className="card-meta card-route-summary">
                  כביש מרכזי: {r.route_summary}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {rideToCancel != null && (
        <div
          className="confirm-modal-backdrop"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-delete-title"
          onClick={() => setRideToCancel(null)}
        >
          <div
            className="confirm-modal-box"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="confirm-delete-title" className="confirm-modal-title">
              האם אני בטוח שאני רוצה למחוק את המסלול?
            </h2>
            <div className="confirm-modal-actions">
              <button
                type="button"
                className="btn btn-outline"
                onClick={(e) => {
                  e.stopPropagation();
                  setRideToCancel(null);
                }}
                disabled={cancelling}
              >
                ביטול
              </button>
              <button
                type="button"
                className="btn btn-danger"
                onClick={(e) => {
                  e.stopPropagation();
                  handleConfirmCancel();
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
