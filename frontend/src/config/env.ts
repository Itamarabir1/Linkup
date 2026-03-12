// בפיתוח: URL יחסי כדי שהבקשות יעברו דרך Vite proxy (ללא CORS). בפרודקשן: VITE_API_URL או fallback
const API_BASE_URL = import.meta.env.DEV
  ? '/api/v1'
  : (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1');

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

// timeout לבקשות API (מילישניות). ברירת מחדל 30 שניות – מונע timeout בהתחלה איטית של השרת
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 30000;

// WebSocket URL for real-time chat and typing (chat-ws). In dev often ws://localhost:8081
const CHAT_WS_URL =
  import.meta.env.VITE_CHAT_WS_URL ||
  (import.meta.env.DEV ? 'ws://localhost:8081' : 'ws://127.0.0.1:8081');

export { API_BASE_URL, GOOGLE_MAPS_API_KEY, API_TIMEOUT_MS, CHAT_WS_URL };
