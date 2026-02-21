import React, { useCallback, useEffect, useState } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { api } from '../api/client';
import type { Ride } from '../types/api';

export default function MyRidesScreen() {
  const navigation = useNavigation<any>();
  const [rides, setRides] = useState<Ride[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchRides = useCallback(async () => {
    try {
      const { data } = await api.get<Ride[]>('/rides/me');
      setRides(Array.isArray(data) ? data : []);
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'טעינת נסיעות נכשלה';
      Alert.alert('שגיאה', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchRides();
  }, [fetchRides]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchRides();
  };

  const renderItem = ({ item }: { item: Ride }) => (
    <View style={styles.card}>
      <Text style={styles.route}>
        {item.origin_name ?? '?'} → {item.destination_name ?? '?'}
      </Text>
      <Text style={styles.meta}>
        {new Date(item.departure_time).toLocaleString('he-IL')} · {item.available_seats} מושבים ·{' '}
        {item.status}
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
      <View style={styles.headerRow}>
        <Text style={styles.title}>הנסיעות שלי</Text>
        <TouchableOpacity style={styles.addButton} onPress={() => navigation.navigate('CreateRide')}>
          <Text style={styles.addButtonText}>+ נסיעה חדשה</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={rides}
        keyExtractor={(item) => String(item.ride_id)}
        renderItem={renderItem}
        contentContainerStyle={rides.length === 0 ? styles.empty : undefined}
        ListEmptyComponent={
          <Text style={styles.emptyText}>אין נסיעות. צור נסיעה חדשה מהלשונית.</Text>
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
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 22, fontWeight: 'bold', textAlign: 'right' },
  addButton: { backgroundColor: '#2563eb', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8 },
  addButtonText: { color: '#fff', fontSize: 14, fontWeight: '600' },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    borderRightWidth: 4,
    borderRightColor: '#2563eb',
  },
  route: { fontSize: 16, fontWeight: '600', textAlign: 'right' },
  meta: { fontSize: 14, color: '#666', marginTop: 4, textAlign: 'right' },
  empty: { flexGrow: 1, justifyContent: 'center' },
  emptyText: { textAlign: 'center', color: '#666', fontSize: 16 },
});
