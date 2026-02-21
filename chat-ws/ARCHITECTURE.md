# ארכיטקטורה - chat-ws vs backend

## עקרון יסוד: הפרדת אחריות

### chat-ws (Go) - שרת WebSocket בלבד
**תפקיד:** העברת הודעות real-time מ-Redis ל-WebSocket clients

**מה כן:**
- ✅ WebSocket connections management
- ✅ JWT authentication
- ✅ Subscribe ל-Redis (`chat:conversation:*`)
- ✅ Forward messages ל-clients

**מה לא:**
- ❌ API endpoints (HTTP)
- ❌ Calendar export
- ❌ AI analysis logic (רק forward אם צריך)
- ❌ Business logic

### backend (Python) - ה-API Server
**תפקיד:** כל ה-API endpoints והלוגיקה העסקית

**מה כן:**
- ✅ REST API endpoints
- ✅ Calendar export (`GET /api/v1/chat/conversations/{id}/calendar.ics`)
- ✅ AI analysis results (`GET /api/v1/chat/conversations/{id}/analysis`)
- ✅ Business logic
- ✅ Database operations

## AI Analysis - איפה?

### אופציה מומלצת: Service נפרד + API endpoint

**AI Analyzer Service** (Python, ב-`chat-ws/ai/service/`):
- מאזין ל-Redis (`chat:conversation:*`)
- מנתח כל הודעה (async, לא חוסם)
- שומר תוצאות ב-DB או Redis cache
- מפרסם תוצאות ל-Redis (`chat:analysis:{conversation_id}`)

**API Endpoint** (ב-backend):
- `GET /api/v1/chat/conversations/{id}/analysis`
- קורא תוצאות מ-DB/Redis
- מחזיר למשתמש

**יתרונות:**
- ✅ לא חוסם את ה-API (ניתוח יכול לקחת זמן)
- ✅ יכול לסקייל בנפרד
- ✅ API endpoint נגיש למשתמשים

## Calendar Export - איפה?

**חייב להיות ב-backend בלבד** - זה API endpoint שהמשתמש מבקש דרך HTTP.

**API Endpoint:**
- `GET /api/v1/chat/conversations/{id}/calendar.ics`
- קורא הודעות מ-DB
- מנתח (או משתמש בתוצאות ניתוח קיימות)
- מייצא ל-iCal
- מחזיר קובץ `.ics`

**מיקום קוד:**
- ✅ `backend/app/domain/chat/calendar/` - לוגיקת calendar (נדרש)
- ✅ `backend/app/api/v1/routers/chat.py` - endpoint
- ❌ `chat-ws/ai/calendar/` - **לא נדרש** (ה-AI service לא משתמש בו)

**למה לא ב-chat-ws?**
- ה-AI Analyzer Service לא צריך לייצא ללוח שנה
- הוא רק מנתח ומפרסם תוצאות
- ה-backend משתמש בתוצאות הניתוח לייצוא ללוח שנה
- שמירת קוד ב-chat-ws יוצרת code duplication מיותר

## זרימה מומלצת

### 1. שליחת הודעה
```
Client → POST /api/v1/chat/conversations/{id}/messages (backend)
       → Backend שומר ב-DB
       → Backend מפרסם ל-Redis (chat:conversation:{id})
       → chat-ws מקבל מ-Redis → שולח ל-WebSocket
       → AI Analyzer מקבל מ-Redis → מנתח → שומר תוצאה
```

### 2. קבלת ניתוח AI
```
Client → GET /api/v1/chat/conversations/{id}/analysis (backend)
       → Backend קורא מ-DB/Redis
       → מחזיר תוצאה
```

### 3. ייצוא ללוח שנה
```
Client → GET /api/v1/chat/conversations/{id}/calendar.ics (backend)
       → Backend קורא הודעות מ-DB
       → Backend מנתח (או משתמש בתוצאות קיימות)
       → Backend מייצא ל-iCal
       → מחזיר קובץ .ics
```

## סיכום

| Feature | Location | Reason |
|---------|----------|--------|
| WebSocket connections | chat-ws (Go) | Real-time, performance |
| REST API endpoints | backend (Python) | Standard API pattern |
| Calendar export | backend (Python) | API endpoint |
| AI analysis service | chat-ws/ai/service (Python) | Async, לא חוסם |
| AI analysis results API | backend (Python) | API endpoint |
| Business logic | backend (Python) | Centralized |
