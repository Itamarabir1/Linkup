# chat-ws – WebSocket server for real-time chat + AI analysis

שרת WebSocket נפרד (Go) לצ'אט real-time + שירות ניתוח AI (Python). עובד יחד עם ה־API ב־Python (FastAPI).

## איך זה משתלב בפרויקט

- **תיקייה נפרדת:** `chat-ws/` ברמת שורש הפרויקט (ליד `backend/` ו־`frontend/`).
- **שלושה processes נפרדים:**
  - **backend (Python):** REST API, DB, שליחת הודעות (POST) + publish ל־Redis.
  - **chat-ws (Go):** WebSocket, Subscribe ל־Redis, דחיפה ל־clients.
  - **ai/service (Python):** ניתוח AI של שיחות צ'אט, מאזין ל-Redis, מפרסם תוצאות.

## מבנה תיקיות

```
chat-ws/
├── cmd/server/          # Entry point של שרת Go
│   └── main.go
├── internal/            # קבצי Go פנימיים
│   ├── hub/            # WebSocket Hub (מפוצל: hub.go, conn.go, handler.go, message.go)
│   ├── redis/          # Redis subscriber
│   ├── auth/           # JWT validation
│   └── config/         # Configuration
├── ai/                  # Python AI analysis
│   ├── analyzer/       # מנתח שיחות (Groq API)
│   │   ├── analyzer.py # ניתוח שיחה אחת
│   │   ├── batch.py    # ניתוח batch
│   │   ├── retry.py    # לוגיקת retry
│   │   ├── client.py   # Groq client
│   │   ├── prompts.py  # Prompts למודל
│   │   └── schema.py   # RideSummary models
│   └── service/        # שירות ניתוח AI (מאזין ל-Redis)
│       ├── service.py   # ChatAnalyzerService (main logic)
│       ├── cache.py     # ניהול cache של הודעות
│       ├── publisher.py # פרסום תוצאות ניתוח
│       ├── config.py    # קונפיגורציה וקבועים
│       └── chat_analyzer_service.py  # Backward compatibility
│       ├── service.py   # ChatAnalyzerService (main logic)
│       ├── cache.py     # ניהול cache של הודעות
│       ├── publisher.py # פרסום תוצאות ניתוח
│       ├── config.py    # קונפיגורציה וקבועים
│       └── chat_analyzer_service.py  # Backward compatibility
└── README.md
```

## הרצה

### דרישות מוקדמות

1. **Redis** חייב לרוץ (אותו Redis של ה־backend).
2. **משתני סביבה** (אותם כמו ב־backend, או ב־`.env` בשורש):
   - `SECRET_KEY` – אותו סוד כמו ב־Python (לאימות JWT).
   - `REDIS_URL` – למשל `redis://localhost:6379/0`.
   - `PORT` – פורט לשרת ה־WS (ברירת מחדל 8081).
   - `GROK_API_KEY` – מפתח API של Groq לניתוח AI (נדרש רק ל-ai/service).

### 1. שרת Go WebSocket

```bash
cd chat-ws
go mod tidy
go run cmd/server/main.go
```

או:

```bash
cd chat-ws/cmd/server
go run main.go
```

### 2. שירות ניתוח AI (Python)

```bash
cd chat-ws/ai
pip install -r requirements.txt
python -m service.chat_analyzer_service
```

### 3. backend (Python) – כרגיל

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## חיבור מהקליינט

- **WebSocket:** `ws://localhost:8081/ws?token=ACCESS_TOKEN`
- ה־token הוא ה־Access Token מה־login (JWT). אותו SECRET_KEY ב־Python וב־Go.

## זרימה

### זרימת הודעות צ'אט

1. לקוח מתחבר ל־`/ws?token=...` → Go מאמת JWT ומשייך חיבור ל־user_id.
2. לקוח שולח הודעה דרך **REST** (POST ל־Python) → Python שומר ב־DB ומפרסם ל־Redis (`chat:conversation:{id}`).
3. Go מקבל מ־Redis → שולח ל־WebSocket של ה־recipient (לפי `recipient_id` ב־payload).

### זרימת ניתוח AI

1. Python (backend) מפרסם הודעת צ'אט ל-Redis (`chat:conversation:{conversation_id}`).
2. **שרת Go** מקבל מ-Redis → שולח ל-WebSocket (מיידי).
3. **שירות Python AI** (נפרד) מקבל מ-Redis → שומר הודעה ב-cache → מנתח את כל השיחה → מפרסם תוצאה ל-Redis (`chat:analysis:{conversation_id}`).
4. (אופציונלי) שרת Go יכול להאזין ל-`chat:analysis:*` → לשלוח תוצאות ניתוח ל-WebSocket.

## ערוצי Redis

- `chat:conversation:{conversation_id}` – הודעות צ'אט (נשלח מ-backend, נשמע ע"י Go WS + AI analyzer)
- `chat:analysis:{conversation_id}` – תוצאות ניתוח AI (נשלח מ-AI analyzer)
- `chat:conversation_cache:{conversation_id}` – cache של הודעות אחרונות (נשמר ע"י AI analyzer)

## פיתוח

### עדכון מבנה Go

אחרי שינוי מבנה תיקיות, ודא שה-imports ב-`cmd/server/main.go` תואמים:

```go
import (
    "linkup/chat-ws/internal/auth"
    "linkup/chat-ws/internal/config"
    "linkup/chat-ws/internal/hub"
    "linkup/chat-ws/internal/redis"
)
```

### בדיקת ניתוח AI

לבדיקת ניתוח AI בנפרד (ללא Redis):

```bash
cd chat-ws/ai
python -c "from analyzer.analyzer import analyze_ride; print(analyze_ride('יוסי: מישהו נוסע מחר? אורן: כן, ב-08:00'))"
```
