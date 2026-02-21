export interface User {
  user_id: number;
  email: string;
  full_name?: string;
  first_name?: string;
  phone_number?: string;
  is_verified?: boolean;
  avatar_url?: string | null;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface Ride {
  ride_id: number;
  driver_id: number;
  origin_name: string | null;
  destination_name: string | null;
  departure_time: string;
  estimated_arrival_time: string | null;
  available_seats: number;
  price: number;
  status: string;
  created_at: string;
  distance_km?: number;
  duration_min?: number;
  route_coords?: number[][];
  /** סיכום המסלול (כביש) – כמו ביצירת הנסיעה */
  route_summary?: string | null;
}

export interface RideSearchResponse {
  rides: Ride[];
  request_id: number | null;
}

export interface PassengerRequest {
  request_id: number;
  passenger_id: number;
  num_passengers: number;
  pickup_name: string | null;
  destination_name: string | null;
  requested_departure_time: string;
  status: string;
  created_at: string;
  is_notification_active: boolean;
}

export interface RidePreviewResponse {
  session_id: string;
  origin_name: string;
  destination_name: string;
  origin_coords: number[];
  destination_coords: number[];
  routes: Array<{
    route_index: number;
    summary: string;
    duration_min: number;
    distance_km: number;
    coords: number[][];
  }>;
}

export interface AddressFromCoordsResponse {
  address: string;
  lat: number;
  lon: number;
}

export interface DriverInfo {
  full_name: string;
  phone_number: string | null;
}

export interface Booking {
  booking_id: number;
  ride_id: number;
  request_id: number;
  passenger_id: number;
  num_seats: number;
  status: string;
  reminder_sent: boolean;
  created_at: string;
  passenger_name?: string | null;
  phone?: string | null;
}

export interface NotificationItem {
  type: string;
  title: string;
  body: string | null;
  created_at: string;
  booking_id: number;
  ride_id: number;
  other_party_name: string | null;
  ride_origin: string | null;
  ride_destination: string | null;
  status: string | null;
}
