import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import type { Group } from '../types/api';
import { getMyGroups } from '../api/groups';
import { useAuth } from './AuthContext';

type GroupContextValue = {
  activeGroup: Group | null;        // null = ציבורי
  setActiveGroup: (g: Group | null) => void;
  myGroups: Group[];
  isLoadingGroups: boolean;
  refreshGroups: () => Promise<void>;
};

const GroupContext = createContext<GroupContextValue | null>(null);

export function GroupProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [activeGroup, setActiveGroupState] = useState<Group | null>(null);
  const [myGroups, setMyGroups] = useState<Group[]>([]);
  const [isLoadingGroups, setIsLoadingGroups] = useState(false);

  const refreshGroups = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsLoadingGroups(true);
    try {
      const groups = await getMyGroups();
      setMyGroups(groups);
    } catch {
      setMyGroups([]);
    } finally {
      setIsLoadingGroups(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    refreshGroups();
  }, [refreshGroups]);

  const setActiveGroup = (g: Group | null) => {
    setActiveGroupState(g);
  };

  return (
    <GroupContext.Provider value={{ activeGroup, setActiveGroup, myGroups, isLoadingGroups, refreshGroups }}>
      {children}
    </GroupContext.Provider>
  );
}

export function useGroup() {
  const ctx = useContext(GroupContext);
  if (!ctx) throw new Error('useGroup must be used within GroupProvider');
  return ctx;
}
