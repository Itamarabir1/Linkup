from typing import List, Tuple, Optional
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, LineString
from geopy.geocoders import Nominatim
import logging

logger = logging.getLogger(__name__)


def get_coords_from_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Sync geocoding: turns an address string into (lat, lon).
    Uses Nominatim (OpenStreetMap). Returns (None, None) on failure.
    """
    try:
        geolocator = Nominatim(user_agent="linkup-backend", timeout=10)
        location = geolocator.geocode(address)
        return (location.latitude, location.longitude) if location else (None, None)
    except Exception as e:
        logger.warning(f"Geocoding failed for '{address}': {e}")
        return (None, None)


def to_geo_point(lat: float, lon: float, srid: int = 4326):
    """
    Technical utility to convert coordinates to PostGIS-friendly format.
    """
    return from_shape(Point(lon, lat), srid=srid)


def to_geo_line(coords: List[Tuple[float, float]], srid: int = 4326):
    """
    Technical utility to convert a list of points to a PostGIS LineString.
    """
    # המרה ל-Lon/Lat עבור תקן GeoJSON/PostGIS
    fmt_coords = [(p[1], p[0]) for p in coords]
    return from_shape(LineString(fmt_coords), srid=srid)
