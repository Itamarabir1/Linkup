import { Outlet, NavLink } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../api/client';
import type { NotificationItem } from '../types/api';
import './Layout.css';

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
        // התראות חדשות = שנוצרו ב-24 שעות האחרונות
        const now = new Date();
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const newCount = data.filter(n => new Date(n.created_at) >= yesterday).length;
        setUnreadNotificationsCount(newCount);
      } catch {
        // ignore errors
      }
    };

    fetchUnreadCount();
    // עדכון כל דקה
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [user?.user_id]);

  return (
    <div className="layout">
      <nav className="nav">
        <NavLink to="/my-rides" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          הנסיעות שלי
        </NavLink>
        <NavLink to="/my-requests" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          בקשות הטרמפ שלי
        </NavLink>
        <NavLink to="/my-bookings" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          הזמנות שלי
        </NavLink>
        <NavLink 
          to="/notifications" 
          className={({ isActive }) => 
            `nav-link ${isActive ? 'active' : ''} ${unreadNotificationsCount > 0 ? 'nav-link-has-notifications' : ''}`
          }
          style={{ position: 'relative' }}
        >
          התראות
          {unreadNotificationsCount > 0 && (
            <span className="nav-notification-badge">{unreadNotificationsCount}</span>
          )}
        </NavLink>
        <NavLink to="/messages" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          הודעות
        </NavLink>
        <NavLink to="/profile" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
          פרופיל
        </NavLink>
      </nav>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
