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
