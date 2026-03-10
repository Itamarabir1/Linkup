-- בדיקת מרחק מוצא הנוסע מהמסלול (request_id=47, ride_id=13)
-- הרץ ב-PostgreSQL כדי לראות אם ST_DWithin היה אמור להחזיר true

SELECT
  pr.request_id,
  r.ride_id,
  ST_Distance(pr.pickup_geom::geography, r.route_coords::geography) AS distance_meters,
  (ST_Distance(pr.pickup_geom::geography, r.route_coords::geography) <= 2000) AS within_2km
FROM passenger_requests pr
CROSS JOIN rides r
WHERE pr.request_id = 47
  AND r.ride_id = 13;
