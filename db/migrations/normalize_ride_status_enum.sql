-- Normalize ride_status: keep only 'open', 'full', 'completed', 'cancelled' (lowercase).
-- Fixes: GET /api/v1/rides/me 500 when DB had 'OPEN' or 'in_progress' (schema had wrong enum values).
--
-- Run once (e.g. psql -U admin -d linkup_app -f db/migrations/normalize_ride_status_enum.sql
-- or Docker: docker exec -i linkup_db psql -U admin -d linkup_app < db/migrations/normalize_ride_status_enum.sql)

-- 1. New enum with only the four values used by the app
CREATE TYPE ride_status_new AS ENUM ('open', 'full', 'completed', 'cancelled');

-- 2. Drop default so we can change column type
ALTER TABLE rides ALTER COLUMN status DROP DEFAULT;

-- 3. Point rides.status to new type: map old values -> new
ALTER TABLE rides
  ALTER COLUMN status TYPE ride_status_new
  USING (
    CASE status::text
      WHEN 'OPEN' THEN 'open'::ride_status_new
      WHEN 'in_progress' THEN 'open'::ride_status_new
      ELSE status::text::ride_status_new
    END
  );

-- 4. Restore default
ALTER TABLE rides ALTER COLUMN status SET DEFAULT 'open'::ride_status_new;

-- 5. Drop old type and rename new one
DROP TYPE ride_status;
ALTER TYPE ride_status_new RENAME TO ride_status;
