import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { api } from '../api/client';
import type { PassengerRequest } from '../types/api';

export default function MyRequestsScreen() {
  const [requests, setRequests] = useState<PassengerRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRequests = useCallback(async () => {
    try {
      const { data } = await api.get<PassengerRequest[]>('/passenger/passengers/me');
      setRequests(Array.isArray(data) ? data : []);
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'טעינת בקשות נכשלה';
      Alert.alert('שגיאה', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchRequests();
  };

  const renderItem = ({ item }: { item: PassengerRequest }) => (
    <View style={styles.card}>
      <Text style={styles.route}>
        {item.pickup_name ?? '?'} → {item.destination_name ?? '?'}
      </Text>
      <Text style={styles.meta}>
        {new Date(item.requested_departure_time).toLocaleString('he-IL')} · סטטוס: {item.status}
      </Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>הבקשות שלי</Text>
      <FlatList
        data={requests}
        keyExtractor={(item) => String(item.request_id)}
        renderItem={renderItem}
        contentContainerStyle={requests.length === 0 ? styles.empty : undefined}
        ListEmptyComponent={
          <Text style={styles.emptyText}>אין בקשות. חפש נסיעות ושמור בקשה.</Text>
        }
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 16, textAlign: 'right' },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderRightWidth: 4,
    borderRightColor: '#059669',
  },
  route: { fontSize: 16, fontWeight: '600', textAlign: 'right' },
  meta: { fontSize: 14, color: '#666', marginTop: 4, textAlign: 'right' },
  empty: { flexGrow: 1, justifyContent: 'center' },
  emptyText: { textAlign: 'center', color: '#666', fontSize: 16 },
});
