import { Outlet, NavLink, Link, useNavigate } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import { MessageCircle, Bell, User, Search, Plus } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../api/client';
import type { NotificationItem } from '../../types/api';
import styles from './Layout.module.css';

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [unreadNotificationsCount, setUnreadNotificationsCount] = useState(0);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);

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
        const count = data.filter((n) => new Date(n.created_at) >= yesterday).length;
        setUnreadNotificationsCount(count);
      } catch {
        // ignore
      }
    };
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 60000);
    return () => clearInterval(interval);
  }, [user?.user_id]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setProfileOpen(false);
    await logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className={styles.layout}>
      <nav className={styles.nav}>
        <div className={styles.navTabs}>
          <NavLink
            to="/my-rides"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            הנסיעות שלי
          </NavLink>
          <NavLink
            to="/my-requests"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            בקשות טרמפ
          </NavLink>
          <NavLink
            to="/my-bookings"
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            הזמנות שלי
          </NavLink>
          <NavLink
            to="/groups"
            end={false}
            className={({ isActive }) =>
              isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink
            }
          >
            קבוצות
          </NavLink>
        </div>

        <div className={styles.navActions}>
          <div className={styles.iconBtnWrapper}>
            <Link to="/messages" className={styles.iconBtn} aria-label="הודעות">
              <MessageCircle size={16} />
              {unreadNotificationsCount > 0 && (
                <span className={styles.notificationDot} aria-hidden />
              )}
            </Link>
          </div>
          <Link
            to="/notifications"
            className={styles.iconBtn}
            aria-label="התראות"
          >
            <Bell size={16} />
          </Link>
          <div className={styles.profileWrap} ref={profileRef}>
            <button
              type="button"
              className={styles.iconBtn}
              onClick={() => setProfileOpen((o) => !o)}
              aria-label="פרופיל"
              aria-expanded={profileOpen}
              aria-haspopup="true"
            >
              <User size={16} />
            </button>
            {profileOpen && (
              <div className={styles.profileDropdown} role="menu">
                <Link
                  to="/profile"
                  className={styles.profileDropdownItem}
                  onClick={() => setProfileOpen(false)}
                >
                  הפרופיל שלי
                </Link>
                <div className={styles.profileDropdownDivider} />
                <button
                  type="button"
                  className={styles.profileDropdownItem}
                  onClick={handleLogout}
                >
                  התנתק
                </button>
              </div>
            )}
          </div>
          <div className={styles.navDivider} />
          <Link to="/search" className={styles.btnSearch}>
            <Search size={14} />
            חפש טרמפ
          </Link>
          <Link to="/create-ride" className={styles.btnCreateRide}>
            <Plus size={14} />
            הצע נסיעה
          </Link>
        </div>
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
