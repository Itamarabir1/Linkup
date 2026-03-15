import { useCallback, useEffect, useState } from 'react';
import { MessageCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useGroup } from '../context/GroupContext';
import { useChat } from '../context/ChatContext';
import { api, openChatByBooking } from '../api/client';
import type { Ride } from '../types/api';
import { formatRideDate } from '../utils/date';
import ConfirmModal from '../components/ConfirmModal/ConfirmModal';
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

const AVATAR_COLORS = ['#6366f1', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0ea5e9'];

function getSource(ride: Ride, myGroups: { group_id: string; name: string }[]): string {
  if (!ride.group_id) return 'ציבורי';
  const g = myGroups.find((x) => x.group_id === ride.group_id);
  return g?.name ?? 'ציבורי';
}

function avatarInitial(name: string): string {
  return (name || 'נ').charAt(0).toUpperCase();
}

export default function MyBookings() {
  const { user } = useAuth();
  const { myGroups } = useGroup();
  const { openChat } = useChat();
  const [activeTab, setActiveTab] = useState<TabKind>('passenger');
  const [passengerList, setPassengerList] = useState<PassengerBookingItem[]>([]);
  const [driverList, setDriverList] = useState<DriverBookingItem[]>([]);
  const [passengerLoading, setPassengerLoading] = useState(true);
  const [driverLoading, setDriverLoading] = useState(false);
  const [error, setError] = useState('');
  const [chatLoading, setChatLoading] = useState<string | null>(null);
  const [bookingToCancel, setBookingToCancel] = useState<string | null>(null);
  const [cancelling, setCancelling] = useState(false);
  const [actionBookingId, setActionBookingId] = useState<string | null>(null);

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
      openChat(conversation.conversation_id);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'פתיחת שיחה נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setChatLoading(null);
    }
  };

  const handleApprove = async (bookingId: string) => {
    if (!user?.user_id) return;
    setActionBookingId(bookingId);
    setError('');
    try {
      await api.patch(`/bookings/${bookingId}/approve`, {}, { params: { driver_id: user.user_id } });
      await fetchDriverBookings();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'אישור הבקשה נכשל';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setActionBookingId(null);
    }
  };

  const handleReject = async (bookingId: string) => {
    if (!user?.user_id) return;
    setActionBookingId(bookingId);
    setError('');
    try {
      await api.patch(`/bookings/${bookingId}/reject`, {}, { params: { driver_id: user.user_id } });
      await fetchDriverBookings();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'דחיית הבקשה נכשלה';
      setError(typeof msg === 'string' ? msg : String(msg));
    } finally {
      setActionBookingId(null);
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
      <div role="tablist" className={styles.pageTabs}>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'passenger'}
          className={activeTab === 'passenger' ? styles.tabActive : styles.tab}
          onClick={() => setActiveTab('passenger')}
        >
          אני נוסע
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'driver'}
          className={activeTab === 'driver' ? styles.tabActive : styles.tab}
          onClick={() => setActiveTab('driver')}
        >
          אני נהג
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
              <div key={bookingId} className={styles.bookingCard}>
                <div className={styles.cardRoute}>
                  {ride.destination_name ?? '?'} ← {ride.origin_name ?? '?'}
                </div>
                <div className={styles.cardMeta}>
                  {formatRideDate(ride.departure_time)} · {statusLabel[bookingStatus] ?? bookingStatus}
                </div>
                {driverName && <div className={styles.cardMeta}>נהג: {driverName}</div>}
                <div className={styles.cardMeta}>{getSource(ride, myGroups)}</div>
                {(bookingStatus === 'pending_approval' || bookingStatus === 'confirmed') && (
                  <div className={styles.bookingCardActions}>
                    <button
                      type="button"
                      className={styles.btnOutline}
                      onClick={() => handleOpenChat(bookingId)}
                      disabled={chatLoading === bookingId}
                    >
                      <MessageCircle size={14} />
                      שיחה עם הנהג
                    </button>
                    <button
                      type="button"
                      className={styles.btnDanger}
                      onClick={() => setBookingToCancel(bookingId)}
                      disabled={cancelling}
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
            driverList.map(({ ride, passengers }) => {
              const pendingCount = passengers.filter((p) => p.status === 'pending_approval').length;
              const confirmedCount = passengers.filter((p) => p.status === 'confirmed').length;
              return (
                <div key={ride.ride_id} className={styles.driverBlock}>
                  <div className={styles.driverBlockHeader}>
                    <div className={styles.cardRoute}>
                      {ride.destination_name ?? '?'} ← {ride.origin_name ?? '?'}
                    </div>
                    <div className={styles.cardMeta}>
                      {formatRideDate(ride.departure_time)} · {ride.available_seats} מושבים
                    </div>
                    <div className={styles.driverBlockCounts}>
                      {pendingCount > 0 && <span>{pendingCount} בקשות</span>}
                      {confirmedCount > 0 && (
                        <span className={pendingCount > 0 ? styles.countSep : ''}>
                          {confirmedCount} מאושרים
                        </span>
                      )}
                    </div>
                  </div>
                  <ul className={styles.passengerList}>
                    {passengers.map((passenger) => (
                      <li key={passenger.bookingId} className={styles.passengerRow}>
                        <div
                          className={styles.passengerAvatar}
                          style={{
                            backgroundColor: AVATAR_COLORS[
                              Math.abs(passenger.passengerName.length) % AVATAR_COLORS.length
                            ],
                          }}
                        >
                          {avatarInitial(passenger.passengerName)}
                        </div>
                        <div className={styles.passengerInfo}>
                          <div className={styles.passengerName}>{passenger.passengerName}</div>
                          <div className={styles.passengerMeta}>
                            {passenger.numSeats} מושב{passenger.numSeats > 1 ? 'ים' : ''}
                            {passenger.pickupName && ` · ${passenger.pickupName}`}
                          </div>
                        </div>
                        <div className={styles.passengerActions}>
                          {passenger.status === 'pending_approval' && (
                            <>
                              <button
                                type="button"
                                className={styles.btnApprove}
                                onClick={() => handleApprove(passenger.bookingId)}
                                disabled={actionBookingId === passenger.bookingId}
                              >
                                אזור
                              </button>
                              <button
                                type="button"
                                className={styles.btnReject}
                                onClick={() => handleReject(passenger.bookingId)}
                                disabled={actionBookingId === passenger.bookingId}
                              >
                                דחה
                              </button>
                            </>
                          )}
                          {passenger.status === 'confirmed' && (
                            <span className={styles.statusConfirmed}>מאושר</span>
                          )}
                          {passenger.status === 'rejected' && (
                            <span className={styles.statusRejected}>נדחה</span>
                          )}
                          {(passenger.status === 'pending_approval' || passenger.status === 'confirmed') && (
                            <button
                              type="button"
                              className={styles.btnChat}
                              onClick={() => handleOpenChat(passenger.bookingId)}
                              disabled={chatLoading === passenger.bookingId}
                              title="שיחה"
                            >
                              <MessageCircle size={14} />
                            </button>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })
          )}
        </div>
      )}

      <ConfirmModal
        open={bookingToCancel != null}
        onClose={() => setBookingToCancel(null)}
        title="האם אתה בטוח שאתה רוצה לבטל את ההזמנה הזו?"
        confirmLabel="אישור"
        variant="danger"
        loading={cancelling}
        onConfirm={async () => {
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
        titleId="confirm-cancel-booking-title"
      />

    </div>
  );
}
