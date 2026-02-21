-- הוספת עמודת סיכום מסלול (כביש) לטבלת rides
-- הרץ אם הטבלה כבר קיימת: psql -U admin -d linkup_app -f db/migrations/add_route_summary_to_rides.sql
ALTER TABLE rides ADD COLUMN IF NOT EXISTS route_summary VARCHAR(255);
