# Alembic – Linkup Backend

מיגרציה אחת. הסכמה המלאה (users, rides, passenger_requests, bookings, groups, group_members, וכו') מוגדרת בקובץ יחיד.

## הרצה

```bash
alembic upgrade head
```

פעם אחת. פועל על DB ריק (יוצר את כל הטבלאות) או על DB קיים (מוסיף רק מה שחסר – idempotent).

## אם ה-DB כבר מכיל מיגרציות ישנות

אם מופיעה שגיאה על revision שלא קיים (למשל `normalize_ride_status`):

- **רק לרשום שה-head כבר הוחל (בלי להריץ שוב):**
  ```sql
  UPDATE alembic_version SET version_num = '001_full_schema';
  ```
- **או לאפס ולהריץ את המיגרציה (תוסיף עמודות/טבלאות שחסרות):**
  ```sql
  DELETE FROM alembic_version;
  ```
  ואז:
  ```bash
  alembic upgrade head
  ```
