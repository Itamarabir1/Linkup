# Google OAuth – מקור אמת אחד

הפרויקט משתמש **ב-client אחד** ל־Google Sign-In. אותו ערך מופיע ב־`frontend/.env` (VITE_GOOGLE_CLIENT_ID) וב־`backend/.env` (GOOGLE_CLIENT_ID).

## Client ID (לא לשנות בלי לעדכן גם ב-Console)

```
852988840047-sp68us8p8oljejkor313uu7pbkskr4fd.apps.googleusercontent.com
```

## ב-Google Cloud Console (אותו client)

APIs & Services → Credentials → פתח את ה-Client ID למעלה.

### Authorized JavaScript origins

כתובת אחת לכל וריאציה, **בלי כפילויות**:

| URI |
|-----|
| `http://localhost:5173` |
| `http://127.0.0.1:5173` |
| `https://localhost:5173` |
| `https://127.0.0.1:5173` |

### Authorized redirect URIs

**אותן ארבע הכתובות בדיוק**, כל אחת פעם אחת:

| URI |
|-----|
| `http://localhost:5173` |
| `http://127.0.0.1:5173` |
| `https://localhost:5173` |
| `https://127.0.0.1:5173` |

- אם יש כפילות (למשל `http://127.0.0.1:5173` פעמיים) – למחוק.
- שמירה: Save.

## בדיקה

- הפרונט רץ על `http://localhost:5173` או `http://127.0.0.1:5173` – וודא שהכתובת הזו מופיעה ב-origins וב-redirect URIs.
- אם משנים Client ID בפרויקט – לעדכן גם ב-Console (או להשאיר ב-Console ורק לעדכן את שני קבצי ה-.env לאותו ערך).
