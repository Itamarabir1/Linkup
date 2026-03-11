import { Outlet, NavLink, Link } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useGroup } from '../../context/GroupContext';
import { api } from '../../api/client';
import type { NotificationItem } from '../../types/api';
import styles from './Layout.module.css';

export default function Layout() {
  const { user } = useAuth();
  const { activeGroup, setActiveGroup, myGroups, isLoadingGroups } = useGroup();
  const [unreadNotificationsCount, setUnreadNotificationsCount] = useState(0);
  const [groupDropdownOpen, setGroupDropdownOpen] = useState(false);
  const groupDropdownRef = useRef<HTMLDivElement>(null);

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

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (groupDropdownRef.current && !groupDropdownRef.current.contains(e.target as Node)) {
        setGroupDropdownOpen(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  return (
    <div className={styles.layout}>
      <nav className={styles.nav}>
        <div className={styles.navStart}>
          <div className={styles.groupDropdown} ref={groupDropdownRef}>
            <button
              type="button"
              className={styles.groupDropdownTrigger}
              onClick={(e) => { e.stopPropagation(); setGroupDropdownOpen((o) => !o); }}
              aria-expanded={groupDropdownOpen}
              aria-haspopup="true"
            >
              {activeGroup ? (
                <>
                  <span className={styles.groupIcon}>👥</span>
                  <span className={styles.groupName}>{activeGroup.name}</span>
                </>
              ) : (
                <>
                  <span className={styles.groupIcon}>🌐</span>
                  <span className={styles.groupName}>ציבורי</span>
                </>
              )}
            </button>
            {groupDropdownOpen && (
              <div className={styles.groupDropdownPanel}>
                <button
                  type="button"
                  className={styles.groupDropdownItem}
                  onClick={() => { setActiveGroup(null); setGroupDropdownOpen(false); }}
                >
                  🌐 ציבורי
                </button>
                {!isLoadingGroups && myGroups.map((g) => (
                  <div key={g.group_id} className={styles.groupDropdownRow}>
                    <button
                      type="button"
                      className={styles.groupDropdownItem}
                      onClick={() => { setActiveGroup(g); setGroupDropdownOpen(false); }}
                    >
                      👥 {g.name}
                    </button>
                    <Link
                      to={`/groups/${g.group_id}`}
                      className={styles.groupDropdownSettings}
                      onClick={() => setGroupDropdownOpen(false)}
                      title="הגדרות קבוצה"
                    >
                      ⚙️
                    </Link>
                  </div>
                ))}
                <Link
                  to="/groups/new"
                  className={styles.groupDropdownNew}
                  onClick={() => setGroupDropdownOpen(false)}
                >
                  ＋ צור קבוצה
                </Link>
              </div>
            )}
          </div>
        </div>
        <div className={styles.navEnd}>
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
        </div>
      </nav>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  );
}
