import { Outlet, NavLink } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import type { NotificationItem } from '../../types/api';
import styles from './Layout.module.css';

export default function Layout() {
  const { user } = useAuth();
  const [unreadNotificationsCount, setUnreadNotificationsCount] = useState(0);

  useEffect(() => {
    if (!user?.user_id) {
      setUnreadNotificationsCount(0);
      return;
    }

    const fetchUnreadCount = async () => {
      try {
        const { data } = await api.get<NotificationItem[]>('/users/me/notifications');
        const now = new Date();
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const newCount = data.filter(n => new Date(n.created_at) >= yesterday).length;
        setUnreadNotificationsCount(newCount);
      } catch {
        // ignore errors
      }
    };

    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [user?.user_id]);

  return (
    <div className={styles.layout}>
      <nav className={styles.nav}>
        <NavLink to="/my-rides" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink)}>
          הנסיעות שלי
        </NavLink>
        <NavLink to="/my-requests" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink)}>
          בקשות הטרמפ שלי
        </NavLink>
        <NavLink to="/my-bookings" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink)}>
          הזמנות שלי
        </NavLink>
        <NavLink
          to="/notifications"
          className={({ isActive }) =>
            `${styles.navLink} ${isActive ? styles.navLinkActive : ''} ${unreadNotificationsCount > 0 ? styles.navLinkHasNotifications : ''} ${isActive && unreadNotificationsCount > 0 ? styles.navLinkHasNotificationsActive : ''}`
          }
          style={{ position: 'relative' }}
        >
          התראות
          {unreadNotificationsCount > 0 && (
            <span className={styles.navNotificationBadge}>{unreadNotificationsCount}</span>
          )}
        </NavLink>
        <NavLink to="/messages" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink)}>
          הודעות
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => (isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink)}>
          פרופיל
        </NavLink>
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
