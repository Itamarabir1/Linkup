import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api, openChatByBooking } from '../api/client';
import type { Ride } from '../types/api';
import { formatDateTimeNoSeconds } from '../utils/date';
import styles from './MyBookings.module.css';

interface BookingRow {
  booking_id: string;
  ride_id: string;
  request_id: string;
  passenger_id: string;
  num_seats: number;
  status: string;
  reminder_sent?: boolean;
  created_at?: string;
  passenger_name?: string;
  phone?: string;
}

/** הזמנות שבהן אני נוסע – מבוקינג + פרטי נסיעה + שם נהג */
interface PassengerBookingItem {
  ride: Ride;
  bookingId: string;
  bookingStatus: string;
  driverName: string | null;
}

/** נוסע בנסיעה שלי (כנהג) */
interface PassengerInRide {
  bookingId: string;
  passengerName: string;
  numSeats: number;
  status: string;
  pickupName?: string | null;
  pickupTime?: string | null;
}

/** הזמנות שבהן אני נהג – נסיעה עם כל הנוסעים שלה */
interface DriverBookingItem {
  ride: Ride;
  passengers: PassengerInRide[];
}

type TabKind = 'driver' | 'passenger';

export default function MyBookings() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabKind>('passenger');
  const [passengerList, setPassengerList] = useState<PassengerBookingItem[]>([]);
  const [driverList, setDriverList] = useState<DriverBookingItem[]>([]);
  const [passengerLoading, setPassengerLoading] = useState(true);
  const [driverLoading, setDriverLoading] = useState(false);
  const [error, setError] = useState('');
  const [chatLoading, setChatLoading] = useState<string | null>(null);
  const [bookingToCancel, setBookingToCancel] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [selectedPassenger, setSelectedPassenger] = useState<PassengerInRide | null>(null);

  const fetchPassengerBookings = useCallback(async () => {
    if (!user?.user_id) return;
    setPassengerLoading(true);
    setError('');
    try {
      const { data: bookings } = await api.get<BookingRow[]>('/bookings/my-bookings', {
        params: { user_id: user.user_id },
      });
      const asPassenger = (Array.isArray(bookings) ? bookings : []).filter(
        (b) => b.passenger_id === user.user_id && (b.status === 'pending_approval' || b.status === 'confirmed')
      );
      const byRideId = new Map<string, BookingRow>();
      asPassenger.forEach((b) => {
        if (!byRideId.has(b.ride_id)) byRideId.set(b.ride_id, b);
      });
      const rideIds = Array.from(byRideId.keys());
      const items: PassengerBookingItem[] = [];
      await Promise.all(
        rideIds.map(async (rideId) => {
          try {
            const [rideRes, driverRes] = await Promise.all([
              api.get<Ride>(`/rides/${rideId}`),
              api.get<{ full_name: string }>(`/passenger/rides/${rideId}/driver-info`).catch(() => null),
            ]);
            const ride = rideRes.data;
            if (ride.status === 'cancelled') return;
            const booking = byRideId.get(rideId)!;
            items.push({
              ride,
              bookingId: booking.booking_id,
              bookingStatus: booking.status,
              driverName: driverRes?.data?.full_name ?? null,
            });
          } catch {
            // skip
          }
        })
      );
      items.sort((a, b) => new Date(a.ride.departure_time).getTime() - new Date(b.ride.departure_time).getTime());
      setPassengerList(items);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'טעינת ההזמנות נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setPassengerLoading(false);
    }
  }, [user?.user_id]);

  const fetchDriverBookings = useCallback(async () => {
    if (!user?.user_id) return;
    setDriverLoading(true);
    setError('');
    try {
      const { data: myRides } = await api.get<Ride[]>('/rides/me');
      const activeRides = (Array.isArray(myRides) ? myRides : []).filter((r) => r.status !== 'cancelled');
      const items: DriverBookingItem[] = [];
      await Promise.all(
        activeRides.map(async (ride) => {
          try {
            const manifestRes = await api.get<{ passengers: Array<{ booking_id: string; passenger_name: string; num_seats: number; status: string; pickup_name?: string | null; pickup_time?: string | null }> }>(
              `/bookings/ride/${ride.ride_id}/manifest`,
              { params: { driver_id: user.user_id } }
            );
            const passengers = manifestRes.data?.passengers ?? [];
            const filteredPassengers = passengers
              .filter((p) => p.status === 'pending_approval' || p.status === 'confirmed')
              .map((p) => ({
                bookingId: p.booking_id,
                passengerName: p.passenger_name ?? 'נוסע',
                numSeats: p.num_seats,
                status: p.status,
                pickupName: p.pickup_name ?? null,
                pickupTime: p.pickup_time ?? null,
              }));
            
            // רק אם יש נוסעים - נוסיף את הנסיעה לרשימה
            if (filteredPassengers.length > 0) {
              items.push({
                ride,
                passengers: filteredPassengers,
              });
            }
          } catch {
            // skip ride
          }
        })
      );
      items.sort((a, b) => new Date(a.ride.departure_time).getTime() - new Date(b.ride.departure_time).getTime());
      setDriverList(items);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'טעינת ההזמנות נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setDriverLoading(false);
    }
  }, [user?.user_id]);

  useEffect(() => {
    fetchPassengerBookings();
  }, [fetchPassengerBookings]);

  useEffect(() => {
    if (activeTab === 'driver') fetchDriverBookings();
  }, [activeTab, fetchDriverBookings]);

  const handleOpenChat = async (bookingId: string) => {
    setChatLoading(bookingId);
    setError('');
    try {
      const conversation = await openChatByBooking(bookingId);
      navigate(`/messages/${conversation.conversation_id}`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'פתיחת שיחה נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setChatLoading(null);
    }
  };

  const statusLabel: Record<string, string> = {
    pending_approval: 'ממתין לאישור',
    confirmed: 'אושר',
    rejected: 'נדחה',
    cancelled: 'בוטל',
  };

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>הזמנות שלי</h1>
      <p className={styles.pageMeta} style={{ color: '#6b7280', marginBottom: '1rem' }}>
        כל הבוקינגים – נסיעות שאישרת (כנהג) או שאושרו לך (כנוסע).
      </p>

      <div role="tablist" className={styles.pageTabs}>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'passenger'}
          className={activeTab === 'passenger' ? `${styles.btn} ${styles.btnPrimary}` : `${styles.btn} ${styles.btnOutline}`}
          onClick={() => setActiveTab('passenger')}
        >
          נוסע
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'driver'}
          className={activeTab === 'driver' ? `${styles.btn} ${styles.btnPrimary}` : `${styles.btn} ${styles.btnOutline}`}
          onClick={() => setActiveTab('driver')}
        >
          נהג
        </button>
      </div>

      {error && <p className={styles.pageError}>{error}</p>}

      {activeTab === 'passenger' && (
        <div className={styles.cardList}>
          {passengerLoading ? (
            <p className={styles.pageLoading}>טוען...</p>
          ) : passengerList.length === 0 ? (
            <p className={styles.emptyText}>אין הזמנות כנוסע. חפש טרמפ ובקש להצטרף.</p>
          ) : (
            passengerList.map(({ ride, bookingId, bookingStatus, driverName }) => (
              <div key={bookingId} className={`${styles.card} ${styles.cardRide} ${styles.cardRideWrap}`}>
                <div className={styles.cardRoute}>
                  {ride.origin_name ?? '?'} → {ride.destination_name ?? '?'}
                </div>
                <div className={styles.cardMeta}>
                  {formatDateTimeNoSeconds(ride.departure_time)} · {ride.available_seats} מושבים ·{' '}
                  {statusLabel[bookingStatus] ?? bookingStatus}
                </div>
                {driverName && <div className={styles.cardMeta}>נהג: {driverName}</div>}
                {(bookingStatus === 'pending_approval' || bookingStatus === 'confirmed') && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #e5e7eb', display: 'grid', gap: '0.5rem' }}>
                    <button
                      type="button"
                      className={`${styles.btn} ${styles.btnOutline}`}
                      onClick={() => handleOpenChat(bookingId)}
                      disabled={chatLoading === bookingId}
                      style={{ width: '100%' }}
                    >
                      {chatLoading === bookingId ? 'פותח שיחה...' : '💬 שיחה עם הנהג'}
                    </button>
                    <button
                      type="button"
                      className={`${styles.btn} ${styles.btnDanger}`}
                      onClick={() => setBookingToCancel(bookingId)}
                      disabled={cancelling}
                      style={{ width: '100%' }}
                    >
                      בטל הזמנה
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === 'driver' && (
        <div className={styles.cardList}>
          {driverLoading ? (
            <p className={styles.pageLoading}>טוען...</p>
          ) : driverList.length === 0 ? (
            <p className={styles.emptyText}>אין הזמנות שאישרת. נוסעים שאישרת יופיעו כאן.</p>
          ) : (
            driverList.map(({ ride, passengers }) => (
              <div key={ride.ride_id} className={`${styles.card} ${styles.cardRide} ${styles.cardRideWrap}`}>
                {/* פרטי הנסיעה - פעם אחת */}
                <div className={styles.cardRoute}>
                  {ride.origin_name ?? '?'} → {ride.destination_name ?? '?'}
                </div>
                <div className={styles.cardMeta}>
                  {formatDateTimeNoSeconds(ride.departure_time)} · {ride.available_seats} מושבים
                </div>
                {ride.route_summary && (
                  <div className={`${styles.cardMeta} ${styles.cardRouteSummary}`}>
                    כביש מרכזי: {ride.route_summary}
                  </div>
                )}
                
                {/* רשימת הנוסעים */}
                {passengers.length > 0 && (
                  <div style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid #e5e7eb' }}>
                    <div style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>
                      נוסעים:
                    </div>
                    {passengers.map((passenger, index) => (
                      <div
                        key={passenger.bookingId}
                        style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '0.75rem 0',
                          borderBottom: index < passengers.length - 1 ? '1px solid #f3f4f6' : 'none',
                        }}
                      >
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                            {passenger.passengerName}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                            {passenger.numSeats} מושב{passenger.numSeats > 1 ? 'ים' : ''} · {statusLabel[passenger.status] ?? passenger.status}
                          </div>
                          {passenger.pickupName && (
                            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginBottom: '0.25rem' }}>
                              תחנת עלייה: {passenger.pickupName}
                            </div>
                          )}
                          {passenger.pickupTime && (
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              שעת עלייה: {formatDateTimeNoSeconds(passenger.pickupTime)}
                            </div>
                          )}
                        </div>
                        {(passenger.status === 'pending_approval' || passenger.status === 'confirmed') && (
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button
                              type="button"
                              className={`${styles.btn} ${styles.btnOutline}`}
                              onClick={() => setSelectedPassenger(passenger)}
                              style={{ fontSize: '0.875rem', padding: '0.375rem 0.75rem' }}
                            >
                              פרטי נוסע
                            </button>
                            <button
                              type="button"
                              className={`${styles.btn} ${styles.btnOutline}`}
                              onClick={() => handleOpenChat(passenger.bookingId)}
                              disabled={chatLoading === passenger.bookingId}
                              style={{ fontSize: '0.875rem', padding: '0.375rem 0.75rem' }}
                            >
                              {chatLoading === passenger.bookingId ? '...' : '💬 שיחה'}
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {bookingToCancel != null && (
        <div
          className={styles.confirmModalBackdrop}
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-cancel-booking-title"
          onClick={() => (!cancelling ? setBookingToCancel(null) : null)}
        >
          <div
            className={styles.confirmModalBox}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="confirm-cancel-booking-title" className={styles.confirmModalTitle}>
              האם אתה בטוח שאתה רוצה לבטל את ההזמנה הזו?
            </h2>
            <div className={styles.confirmModalActions}>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnOutline}`}
                onClick={() => setBookingToCancel(null)}
                disabled={cancelling}
              >
                ביטול
              </button>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnDanger}`}
                onClick={async () => {
                  if (bookingToCancel == null) return;
                  setCancelling(true);
                  setError('');
                  try {
                    await api.post(`/bookings/${bookingToCancel}/cancel`);
                    setBookingToCancel(null);
                    await fetchPassengerBookings();
                  } catch (err: unknown) {
                    const msg =
                      (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
                      'ביטול ההזמנה נכשל';
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

      {selectedPassenger && (
        <div
          className={styles.confirmModalBackdrop}
          role="dialog"
          aria-modal="true"
          aria-labelledby="passenger-details-title"
          onClick={() => setSelectedPassenger(null)}
        >
          <div
            className={styles.confirmModalBox}
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '500px' }}
          >
            <h2 id="passenger-details-title" className={styles.confirmModalTitle}>
              פרטי נוסע
            </h2>
            <div style={{ padding: '1rem 0' }}>
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>שם:</div>
                <div style={{ color: '#6b7280' }}>{selectedPassenger.passengerName}</div>
              </div>
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>מספר מושבים:</div>
                <div style={{ color: '#6b7280' }}>{selectedPassenger.numSeats} מושב{selectedPassenger.numSeats > 1 ? 'ים' : ''}</div>
              </div>
              {selectedPassenger.pickupName && (
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>תחנת עלייה:</div>
                  <div style={{ color: '#6b7280' }}>{selectedPassenger.pickupName}</div>
                </div>
              )}
              {selectedPassenger.pickupTime && (
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>שעת עלייה:</div>
                  <div style={{ color: '#6b7280' }}>{formatDateTimeNoSeconds(selectedPassenger.pickupTime)}</div>
                </div>
              )}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontWeight: 600, marginBottom: '0.5rem', color: '#374151' }}>סטטוס:</div>
                <div style={{ color: '#6b7280' }}>
                  {statusLabel[selectedPassenger.status] ?? selectedPassenger.status}
                </div>
              </div>
            </div>
            <div className={styles.confirmModalActions}>
              <button
                type="button"
                className={`${styles.btn} ${styles.btnPrimary}`}
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPassenger(null);
                }}
              >
                סגור
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
