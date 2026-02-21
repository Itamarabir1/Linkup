import { useState, useCallback } from 'react';
import * as Location from 'expo-location';
import { api } from '../api/client';

/**
 * "השתמש במיקום שלי" – מקבל הרשאה, קורא קואורדינטות, וממיר לכתובת דרך GET /geo/address.
 * דורש משתמש מחובר (טוקן).
 */
export function useGeo() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAddressFromLocation = useCallback(async (): Promise<{ address: string; lat: number; lon: number } | null> => {
    setLoading(true);
    setError(null);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        setError('אין הרשאה למיקום');
        return null;
      }
      const location = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.Balanced,
      });
      const { latitude, longitude } = location.coords;
      const { data } = await api.get<{ address: string; lat: number; lon: number }>(
        '/geo/address',
        { params: { lat: latitude, lon: longitude } }
      );
      return data;
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'שגיאה במיקום';
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg));
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { fetchAddressFromLocation, loading, error };
}
