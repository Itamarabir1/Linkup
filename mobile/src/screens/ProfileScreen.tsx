import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import { useAuth } from '../context/AuthContext';

export default function ProfileScreen() {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    Alert.alert('התנתקות', 'האם להתנתק?', [
      { text: 'ביטול', style: 'cancel' },
      { text: 'התנתק', style: 'destructive', onPress: logout },
    ]);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>פרופיל</Text>
      {user && (
        <View style={styles.card}>
          <Text style={styles.label}>שם</Text>
          <Text style={styles.value}>{user.full_name || user.first_name || user.email}</Text>
          <Text style={styles.label}>אימייל</Text>
          <Text style={styles.value}>{user.email}</Text>
          {user.phone_number ? (
            <>
              <Text style={styles.label}>טלפון</Text>
              <Text style={styles.value}>{user.phone_number}</Text>
            </>
          ) : null}
        </View>
      )}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>התנתק</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 16 },
  title: { fontSize: 22, fontWeight: 'bold', marginBottom: 16, textAlign: 'right' },
  card: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 24,
  },
  label: { fontSize: 12, color: '#666', marginTop: 12, textAlign: 'right' },
  value: { fontSize: 16, textAlign: 'right' },
  logoutButton: {
    backgroundColor: '#dc2626',
    paddingVertical: 14,
    borderRadius: 8,
    alignItems: 'center',
  },
  logoutText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
