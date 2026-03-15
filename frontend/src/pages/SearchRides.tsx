import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import type { Ride, DriverInfo, RideSearchResponse } from '../types/api';
import { formatDateTimeNoSeconds } from '../utils/date';
import { useAuth } from '../context/AuthContext';
import styles from './SearchRides.module.css';

export default function SearchRides() {
  const { user } = useAuth();
  const [pickup, setPickup] = useState('');
  const [destination, setDestination] = useState('');
  const [searchRadius, setSearchRadius] = useState(1000);
  const [departureDate, setDepartureDate] = useState('');
  const [departureTime, setDepartureTime] = useState('');
  const [results, setResults] = useState<Ride[]>([]);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState('');
  const [locationLoading, setLocationLoading] = useState(false);
  const [driverInfoMap, setDriverInfoMap] = useState<Record<string, DriverInfo>>({});
  const [loadingDriverRideId, setLoadingDriverRideId] = useState<string | null>(null);
  const [sendingRequestRideId, setSendingRequestRideId] = useState<string | null>(null);
  const [requestSuccessRideId, setRequestSuccessRideId] = useState<string | null>(null);
  const [requestErrorRideId, setRequestErrorRideId] = useState<string | null>(null);
  const [requestErrorMessage, setRequestErrorMessage] = useState<string>('');

  const fillPickupFromMyLocation = () => {
    if (!navigator.geolocation) {
      setError('הדפדפן לא תומך במיקום');
      return;
    }
    setLocationLoading(true);
    setError('');
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        try {
          const { data } = await api.get<{ address: string }>('/geo/address', {
            params: { lat, lon },
          });
          setPickup(data.address ?? '');
        } catch {
          setError('לא נמצאה כתובת למיקום זה');
        } finally {
          setLocationLoading(false);
        }
      },
      () => {
        setError('לא ניתן לקבל מיקום – בדוק הרשאות');
        setLocationLoading(false);
      },
      { timeout: 10000 }
    );
  };

  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pickup.trim() || !destination.trim()) {
      setError('נא למלא מוצא ויעד');
      return;
    }
    setError('');
    setSearching(true);
    setResults([]);
    setCurrentRequestId(null);
    setRequestSuccessRideId(null);
    setDriverInfoMap({});
    try {
      const params: Record<string, string | number | undefined> = {
        pickup_name: pickup.trim(),
        destination_name: destination.trim(),
        search_radius: searchRadius,
      };
      if (departureDate && departureTime) {
        params.departure_time = new Date(`${departureDate}T${departureTime}`).toISOString();
      }
      const { data } = await api.get<RideSearchResponse>(
        '/passenger/passengers/search-rides',
        { params }
      );
      setResults(Array.isArray(data.rides) ? data.rides : []);
      setCurrentRequestId(data.request_id || null);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || 'חיפוש נכשל';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setSearching(false);
    }
  };

  const fetchDriverInfo = async (rideId: string) => {
    setLoadingDriverRideId(rideId);
    setError('');
    try {
      const { data } = await api.get<DriverInfo>(`/passenger/rides/${rideId}/driver-info`);
      setDriverInfoMap((prev) => ({ ...prev, [rideId]: data }));
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { message?: string; detail?: string } } })?.response?.data
          ?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'לא ניתן לטעון פרטי נהג';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setLoadingDriverRideId(null);
    }
  };

  const sendRequestToJoin = async (r: Ride) => {
    if (!pickup.trim() || !destination.trim()) {
      setError('נא למלא מוצא ויעד לפני שליחת בקשה');
      return;
    }
    setSendingRequestRideId(r.ride_id);
    setRequestErrorRideId(null);
    setRequestErrorMessage('');
    setError('');
    try {
      await api.post('/passenger/passengers/request-ride-from-search', {
        ride_id: r.ride_id,
        request_id: currentRequestId,
        pickup_name: pickup.trim(),
        destination_name: destination.trim(),
        num_seats: 1,
      });
      setRequestSuccessRideId(r.ride_id);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      if (status === 401) {
        setError('פג תוקף ההתחברות – אנא התחבר מחדש כדי לשלוח בקשה.');
        return;
      }
      if (status === 409) {
        const msg =
          (err as { response?: { data?: { message?: string } } })?.response?.data?.message ||
          'המקום התמלא. נסה נסיעה אחרת.';
        setRequestErrorRideId(r.ride_id);
        setRequestErrorMessage(typeof msg === 'string' ? msg : 'המקום התמלא. נסה נסיעה אחרת.');
        setError(typeof msg === 'string' ? msg : 'המקום התמלא. נסה נסיעה אחרת.');
        return;
      }
      const msg =
        (err as { response?: { data?: { message?: string; detail?: string } } })?.response?.data
          ?.message ||
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        'שליחת הבקשה נכשלה';
      setRequestErrorRideId(r.ride_id);
      setRequestErrorMessage(typeof msg === 'string' ? msg : String(msg));
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setSendingRequestRideId(null);
    }
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>חפש טרמפ</h1>
      <p className={styles.pageMeta} style={{ color: '#6b7280', marginBottom: '1rem' }}>
        מוצא, יעד, רדיוס חיפוש (מטרים) וזמן יציאה אופציונלי – כמו בבקאנד.
      </p>
      <form onSubmit={search} className={styles.formBlock}>
        {error && (
          <p className={styles.pageError}>
            {error}
            {error.includes('פג תוקף') && (
              <> <Link to="/login" style={{ fontWeight: 600 }}>התחבר מחדש</Link></>
            )}
          </p>
        )}
        <div className={styles.formRowWithBtn}>
          <input
            type="text"
            placeholder="מוצא (כתובת איסוף)"
            value={pickup}
            onChange={(e) => setPickup(e.target.value)}
            className={styles.formInput}
          />
          <button
            type="button"
            className={`${styles.btn} ${styles.btnOutline}`}
            onClick={fillPickupFromMyLocation}
            disabled={locationLoading}
          >
            {locationLoading ? '...' : 'מיקום עצמי'}
          </button>
        </div>
        <input
          type="text"
          placeholder="יעד (כתובת)"
          value={destination}
          onChange={(e) => setDestination(e.target.value)}
          className={styles.formInput}
        />
        <label className={styles.formLabel}>רדיוס חיפוש (מטרים)</label>
        <input
          type="number"
          min={100}
          value={searchRadius}
          onChange={(e) => setSearchRadius(parseInt(e.target.value, 10) || 1000)}
          className={styles.formInput}
        />
        <label className={styles.formLabel}>תאריך יציאה (אופציונלי – ריק = מעכשיו)</label>
        <input
          type="date"
          value={departureDate}
          onChange={(e) => setDepartureDate(e.target.value)}
          className={styles.formInput}
        />
        <label className={styles.formLabel}>שעת יציאה (אופציונלי)</label>
        <input
          type="time"
          value={departureTime}
          onChange={(e) => setDepartureTime(e.target.value)}
          className={styles.formInput}
        />
        <button
          type="submit"
          className={`${styles.btn} ${styles.btnSuccess}`}
          disabled={searching}
        >
          {searching ? 'מחפש...' : 'חפש'}
        </button>
      </form>
      <div className={styles.cardList}>
        {results.length === 0 && pickup && destination && !searching ? (
          <div>
            <p className={styles.emptyText} style={{ marginBottom: '0.5rem' }}>לא נמצאו נסיעות.</p>
            {user && currentRequestId ? (
              <p className={styles.pageMeta} style={{ color: '#6b7280', fontSize: '0.9rem', textAlign: 'center', padding: '0.5rem', background: '#f0f9ff', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
                ✅ נסיעתך נכנסה ל-DB ותקבל התראות כאשר יימצאו נסיעות מתאימות.
              </p>
            ) : user ? (
              <p className={styles.pageMeta} style={{ color: '#6b7280', fontSize: '0.9rem', textAlign: 'center', padding: '0.5rem', background: '#f0f9ff', borderRadius: '8px', border: '1px solid #bfdbfe' }}>
                ✅ פרטי החיפוש שלך נשמרו ותקבל התראות כאשר יימצאו נסיעות מתאימות.
              </p>
            ) : null}
          </div>
        ) : (
          results.map((r) => (
            <div key={r.ride_id} className={styles.card}>
              <div className={styles.cardRoute}>
                {r.origin_name ?? '?'} → {r.destination_name ?? '?'}
              </div>
              <div className={styles.cardMeta}>
                {formatDateTimeNoSeconds(r.departure_time)} ·{' '}
                {r.available_seats} מושבים
              </div>
              {r.route_summary && (
                <div className={`${styles.cardMeta} ${styles.cardRouteSummary}`}>
                  כביש מרכזי: {r.route_summary}
                </div>
              )}
              <div className={styles.cardActions} style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  className={`${styles.btn} ${styles.btnOutline}`}
                  onClick={() => fetchDriverInfo(r.ride_id)}
                  disabled={loadingDriverRideId === r.ride_id}
                >
                  {loadingDriverRideId === r.ride_id ? '...' : 'הצג פרטי הנהג'}
                </button>
                <button
                  type="button"
                  className={`${styles.btn} ${styles.btnSuccess}`}
                  onClick={() => sendRequestToJoin(r)}
                  disabled={sendingRequestRideId !== null || requestSuccessRideId === r.ride_id}
                >
                  {requestSuccessRideId === r.ride_id
                    ? 'הבקשה נשלחה'
                    : sendingRequestRideId === r.ride_id
                      ? 'מעבד...'
                      : 'בקש להצטרפות לנסיעה'}
                </button>
              </div>
              {requestErrorRideId === r.ride_id && requestErrorMessage && (
                <p className={styles.pageError} style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                  {requestErrorMessage}
                </p>
              )}
              {driverInfoMap[r.ride_id] && (
                <div className={styles.cardMeta} style={{ marginTop: '0.5rem', padding: '0.5rem', background: 'var(--surface)', borderRadius: 6 }}>
                  <strong>נהג:</strong> {driverInfoMap[r.ride_id].full_name}
                  {driverInfoMap[r.ride_id].phone_number && (
                    <> · <a href={`tel:${driverInfoMap[r.ride_id].phone_number}`}>{driverInfoMap[r.ride_id].phone_number}</a></>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
