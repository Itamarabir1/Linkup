/* Minimal types for Google Maps JavaScript API (loaded via script tag) */
declare namespace google {
  namespace maps {
    class Map {
      constructor(mapDiv: HTMLElement, opts?: MapOptions);
      fitBounds(bounds: LatLngBounds, padding?: number | Padding): void;
    }
    interface MapOptions {
      zoom?: number;
      center?: LatLngLiteral;
      mapTypeControl?: boolean;
      fullscreenControl?: boolean;
      zoomControl?: boolean;
    }
    interface LatLngLiteral {
      lat: number;
      lng: number;
    }
    class LatLngBounds {
      extend(point: LatLngLiteral): void;
    }
    class Polyline {
      constructor(opts?: PolylineOptions);
    }
    interface PolylineOptions {
      path?: LatLngLiteral[];
      geodesic?: boolean;
      strokeColor?: string;
      strokeOpacity?: number;
      strokeWeight?: number;
      map?: Map;
    }
    class Marker {
      constructor(opts?: MarkerOptions);
    }
    interface MarkerOptions {
      position?: LatLngLiteral;
      map?: Map;
      title?: string;
      label?: { text: string; color: string };
    }
    interface Padding {
      top?: number;
      right?: number;
      bottom?: number;
      left?: number;
    }
  }
}
