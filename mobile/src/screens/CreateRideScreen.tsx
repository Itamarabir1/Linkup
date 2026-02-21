import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  ScrollView,
} from 'react-native';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { RidePreviewResponse } from '../types/api';

export default function CreateRideScreen({ navigation }: { navigation: any }) {
  const { user } = useAuth();
  const [originName, setOriginName] = useState('');
  const [destinationName, setDestinationName] = useState('');
  const [departureTime, setDepartureTime] = useState('');
  const [seats, setSeats] = useState('4');
  const [loading, setLoading] = useState(false);
  const [preview, setPreview] = useState<RidePreviewResponse | null>(null);
  const [creating, setCreating] = useState(false);

  const requestPreview = async () => {
    if (!originName.trim() || !destinationName.trim()) {
      Alert.alert('שגיאה', 'נא למלא מוצא ויעד');
      return;
    }
    const dep = departureTime ? new Date(departureTime) : new Date(Date.now() + 3600000);
    if (isNaN(dep.getTime()) || dep <= new Date()) {
      Alert.alert('שגיאה', 'נא לבחור זמן יציאה בעתיד');
      return;
    }
    setLoading(true);
    setPreview(null);
    try {
      const { data } = await api.post<RidePreviewResponse>('/rides/preview-routes', {
        driver_id: user?.user_id ?? 0,
        origin_name: originName.trim(),
        destination_name: destinationName.trim(),
        departure_time: dep.toISOString(),
        available_seats: parseInt(seats, 10) || 4,
        price: 0,
      });
      setPreview(data);
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'תצוגה מקדימה נכשלה';
      Alert.alert('שגיאה', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setLoading(false);
    }
  };

  const createRide = async () => {
    if (!preview?.session_id) return;
    setCreating(true);
    try {
      await api.post('/rides/', {
        session_id: preview.session_id,
        selected_route_index: 0,
      });
      Alert.alert('הצלחה', 'הנסיעה נוצרה', [
        { text: 'אישור', onPress: () => navigation.navigate('MyRides') },
      ]);
      setPreview(null);
    } catch (e: any) {
      const msg = e.response?.data?.detail || 'יצירת נסיעה נכשלה';
      Alert.alert('שגיאה', typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setCreating(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>יצירת נסיעה</Text>
      <TextInput
        style={styles.input}
        placeholder="מוצא"
        placeholderTextColor="#999"
        value={originName}
        onChangeText={setOriginName}
        textAlign="right"
      />
      <TextInput
        style={styles.input}
        placeholder="יעד"
        placeholderTextColor="#999"
        value={destinationName}
        onChangeText={setDestinationName}
        textAlign="right"
      />
      <TextInput
        style={styles.input}
        placeholder="זמן יציאה (ISO או תאריך)"
        placeholderTextColor="#999"
        value={departureTime}
        onChangeText={setDepartureTime}
        textAlign="right"
      />
      <TextInput
        style={styles.input}
        placeholder="מושבים"
        placeholderTextColor="#999"
        value={seats}
        onChangeText={setSeats}
        keyboardType="number-pad"
        textAlign="right"
      />
      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={requestPreview}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>תצוגה מקדימה</Text>
        )}
      </TouchableOpacity>

      {preview && (
        <View style={styles.preview}>
          <Text style={styles.previewTitle}>מסלול: {preview.routes?.[0]?.summary ?? 'נבחר'}</Text>
          <Text style={styles.meta}>
            {preview.routes?.[0]?.distance_km ?? 0} ק"מ · {preview.routes?.[0]?.duration_min ?? 0} דק'
          </Text>
          <TouchableOpacity
            style={[styles.button, styles.createButton, creating && styles.buttonDisabled]}
            onPress={createRide}
            disabled={creating}
          >
            {creating ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>צור נסיעה</Text>
            )}
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 16, paddingBottom: 32 },
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
    backgroundColor: '#2563eb',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  createButton: { backgroundColor: '#059669', marginTop: 16 },
  buttonDisabled: { opacity: 0.7 },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: '600' },
  preview: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginTop: 24,
    borderRightWidth: 4,
    borderRightColor: '#2563eb',
  },
  previewTitle: { fontSize: 16, fontWeight: '600', textAlign: 'right' },
  meta: { fontSize: 14, color: '#666', marginTop: 4, textAlign: 'right' },
});
