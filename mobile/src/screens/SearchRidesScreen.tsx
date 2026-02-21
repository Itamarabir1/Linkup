import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { api } from '../api/client';
import type { Ride } from '../types/api';

export default function SearchRidesScreen() {
  const [pickup, setPickup] = useState('');
  const [destination, setDestination] = useState('');
  const [results, setResults] = useState<Ride[]>([]);
  const [searching, setSearching] = useState(false);

  const search = async () => {
    if (!pickup.trim() || !destination.trim()) {
      Alert.alert('שגיאה', 'נא למלא מוצא ויעד');
      return;
    }
    setSearching(true);
    setResults([]);
    try {
      const { data } = await api.get<Ride[]>('/passenger/passengers/search-rides', {
        params: {
          pickup_name: pickup.trim(),
          destination_name: destination.trim(),
          search_radius: 1000,
        },
      });
      setResults(Array.isArray(data) ? data : []);
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'חיפוש נכשל';
      Alert.alert('שגיאה', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setSearching(false);
    }
  };

  const renderItem = ({ item }: { item: Ride }) => (
    <View style={styles.card}>
      <Text style={styles.route}>
        {item.origin_name ?? '?'} → {item.destination_name ?? '?'}
      </Text>
      <Text style={styles.meta}>
        {new Date(item.departure_time).toLocaleString('he-IL')} · {item.available_seats} מושבים
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>חיפוש נסיעות</Text>
      <TextInput
        style={styles.input}
        placeholder="מוצא"
        placeholderTextColor="#999"
        value={pickup}
        onChangeText={setPickup}
        textAlign="right"
      />
      <TextInput
        style={styles.input}
        placeholder="יעד"
        placeholderTextColor="#999"
        value={destination}
        onChangeText={setDestination}
        textAlign="right"
      />
      <TouchableOpacity
        style={[styles.button, searching && styles.buttonDisabled]}
        onPress={search}
        disabled={searching}
      >
        {searching ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>חפש</Text>
        )}
      </TouchableOpacity>
      <FlatList
        data={results}
        keyExtractor={(item) => String(item.ride_id)}
        renderItem={renderItem}
        contentContainerStyle={results.length === 0 ? styles.empty : undefined}
        ListEmptyComponent={
          !searching && pickup && destination ? (
            <Text style={styles.emptyText}>לא נמצאו נסיעות. נסה להרחיב רדיוס או תאריך.</Text>
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 16, textAlign: 'right' },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 12,
    fontSize: 16,
    textAlign: 'right',
    backgroundColor: '#fff',
  },
  button: {
    backgroundColor: '#059669',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16,
  },
  buttonDisabled: { opacity: 0.7 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  route: { fontSize: 16, fontWeight: '600', textAlign: 'right' },
  meta: { fontSize: 14, color: '#666', marginTop: 4, textAlign: 'right' },
  empty: { flexGrow: 1 },
  emptyText: { textAlign: 'center', color: '#666', fontSize: 14, marginTop: 24 },
});
