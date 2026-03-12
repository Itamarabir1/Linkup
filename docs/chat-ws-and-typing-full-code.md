# קוד מלא – צ'אט WebSocket ואינדיקציית "מקליד..."

מסמך זה מכיל את הקוד המלא של כל הקבצים הרלוונטיים.  
אפשר לפתוח את הקובץ ב-Microsoft Word (פתח → בחר קובץ .md) ולשמור כ-DOCX.

---

## 1. chat-ws/internal/auth/jwt.go

```go
package auth

import (
	"fmt"

	"github.com/golang-jwt/jwt/v5"
)

// Claims for access token (same structure as Python: sub = user_id, UUID string).
type claims struct {
	Sub string `json:"sub"`
	jwt.RegisteredClaims
}

// ValidateToken parses the JWT and returns user_id (sub) as string. Supports UUID from Python backend.
func ValidateToken(tokenString, secretKey, alg string) (userID string, err error) {
	if secretKey == "" {
		return "", fmt.Errorf("SECRET_KEY is required")
	}
	token, err := jwt.ParseWithClaims(tokenString, &claims{}, func(t *jwt.Token) (interface{}, error) {
		if t.Method.Alg() != alg {
			return nil, fmt.Errorf("unexpected alg: %s", t.Method.Alg())
		}
		return []byte(secretKey), nil
	})
	if err != nil {
		return "", err
	}
	c, ok := token.Claims.(*claims)
	if !ok || !token.Valid {
		return "", fmt.Errorf("invalid token")
	}
	if c.Sub == "" {
		return "", fmt.Errorf("empty sub")
	}
	return c.Sub, nil
}
```

---

## 2. chat-ws/internal/hub/hub.go

```go
package hub

import (
	"context"
	"sync"

	"github.com/redis/go-redis/v9"
)

// Hub maps user_id (UUID string) -> list of connections (one user can have multiple devices).
type Hub struct {
	mu          sync.RWMutex
	users       map[string][]*Conn
	redisClient *redis.Client
}

// NewHub creates a Hub. redisClient is used to publish typing events; can be nil (typing disabled).
func NewHub(redisClient *redis.Client) *Hub {
	return &Hub{
		users:       make(map[string][]*Conn),
		redisClient: redisClient,
	}
}

// Register adds a connection for userID.
func (h *Hub) Register(userID string, c *Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.users[userID] = append(h.users[userID], c)
}

// Unregister removes a connection.
func (h *Hub) Unregister(userID string, c *Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()
	list := h.users[userID]
	for i, x := range list {
		if x == c {
			h.users[userID] = append(list[:i], list[i+1:]...)
			if len(h.users[userID]) == 0 {
				delete(h.users, userID)
			}
			break
		}
	}
}

// SendToUser sends a JSON message to all connections of the given user.
func (h *Hub) SendToUser(userID string, payload []byte) {
	h.mu.RLock()
	conns := h.users[userID]
	// copy so we don't hold lock while writing
	if len(conns) > 0 {
		conns = append([]*Conn(nil), conns...)
	}
	h.mu.RUnlock()
	for _, c := range conns {
		select {
		case c.Send <- payload:
		default:
			// buffer full, skip (or close conn)
		}
	}
}

// PublishTyping publishes a typing event to Redis channel chat:typing:{conversation_id}. No-op if redisClient is nil.
func (h *Hub) PublishTyping(ctx context.Context, channel string, payload []byte) error {
	if h.redisClient == nil {
		return nil
	}
	return h.redisClient.Publish(ctx, channel, payload).Err()
}
```

---

## 3. chat-ws/internal/hub/conn.go

```go
package hub

import (
	"log"
	"time"

	"github.com/gorilla/websocket"
)

const (
	// Time allowed to write a message to the peer.
	writeWait = 10 * time.Second

	// Time allowed to read the next pong message from the peer.
	pongWait = 60 * time.Second

	// Send pings to peer with this period. Must be less than pongWait.
	pingPeriod = (pongWait * 9) / 10

	// Maximum message size allowed from peer.
	maxMessageSize = 512
)

// Conn represents a WebSocket connection for a user.
type Conn struct {
	UserID string
	Conn   *websocket.Conn
	Send   chan []byte
}

// RunWritePump pumps messages from the hub to the websocket connection.
// A goroutine running RunWritePump is started for each connection.
func (c *Conn) RunWritePump() {
	ticker := time.NewTicker(pingPeriod)
	defer func() {
		ticker.Stop()
		c.Conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			c.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if !ok {
				// The hub closed the channel.
				c.Conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.Conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			// Add queued chat messages to the current websocket message.
			n := len(c.Send)
			for i := 0; i < n; i++ {
				w.Write([]byte{'\n'})
				w.Write(<-c.Send)
			}

			if err := w.Close(); err != nil {
				return
			}

		case <-ticker.C:
			c.Conn.SetWriteDeadline(time.Now().Add(writeWait))
			if err := c.Conn.WriteMessage(websocket.PingMessage, nil); err != nil {
				log.Printf("websocket ping error for user %s: %v", c.UserID, err)
				return
			}
		}
	}
}
```

---

## 4. chat-ws/internal/hub/message.go

```go
package hub

// ChatMessage is the payload we send over WS (same as Redis payload from Python). IDs are UUID strings.
type ChatMessage struct {
	MessageID      int    `json:"message_id"`
	ConversationID string `json:"conversation_id"`
	SenderID       string `json:"sender_id"`
	RecipientID    string `json:"recipient_id"`
	Body           string `json:"body"`
	CreatedAt      string `json:"created_at"`
}

// TypingPayload is sent when a user starts typing. Published to chat:typing:{conversation_id}.
type TypingPayload struct {
	Type            string `json:"type"` // "typing_start"
	UserID          string `json:"user_id"`
	ConversationID  string `json:"conversation_id"`
	RecipientID     string `json:"recipient_id"`
	FullName        string `json:"full_name,omitempty"`
}
```

---

## 5. chat-ws/internal/hub/handler.go

```go
package hub

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/gorilla/websocket"

	"linkup/chat-ws/internal/auth"
	"linkup/chat-ws/internal/config"
)

var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // allow same-origin or set your frontend origin
	},
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

// HandleWS upgrades HTTP to WebSocket. Query: token=JWT. Validates token and registers connection.
func (h *Hub) HandleWS(cfg config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token := r.URL.Query().Get("token")
		if token == "" {
			http.Error(w, "missing token", http.StatusUnauthorized)
			return
		}
		userID, err := auth.ValidateToken(token, cfg.SecretKey, cfg.JWTAlg)
		if err != nil {
			http.Error(w, "invalid token", http.StatusUnauthorized)
			return
		}
		conn, err := upgrader.Upgrade(w, r, nil)
		if err != nil {
			log.Printf("ws upgrade: %v", err)
			return
		}
		c := &Conn{UserID: userID, Conn: conn, Send: make(chan []byte, 256)}
		h.Register(userID, c)
		defer func() {
			h.Unregister(userID, c)
			close(c.Send)
		}()
		go c.RunWritePump()
		// Block until client closes.
		for {
			if _, _, err := conn.ReadMessage(); err != nil {
				return
			}
		}
	}
}

// PublishChatMessage is called when we receive from Redis; payload is JSON string.
func (h *Hub) PublishChatMessage(payload []byte) {
	var msg ChatMessage
	if err := json.Unmarshal(payload, &msg); err != nil {
		log.Printf("redis chat payload unmarshal: %v", err)
		return
	}
	// Send to recipient (1:1). Optionally also echo to sender if needed.
	h.SendToUser(msg.RecipientID, payload)
}
```

---

## 6. chat-ws/internal/redis/subscriber.go

```go
package redis

import (
	"context"
	"log"

	"github.com/redis/go-redis/v9"

	"linkup/chat-ws/internal/hub"
)

const ChatChannelPattern = "chat:conversation:*"

// RunSubscriber subscribes to chat:conversation:* and forwards messages to the Hub.
func RunSubscriber(ctx context.Context, redisURL string, h *hub.Hub) {
	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		log.Printf("redis parse URL: %v", err)
		return
	}
	client := redis.NewClient(opt)
	defer client.Close()
	pubsub := client.PSubscribe(ctx, ChatChannelPattern)
	defer pubsub.Close()
	ch := pubsub.Channel()
	for {
		select {
		case <-ctx.Done():
			return
		case msg, ok := <-ch:
			if !ok {
				return
			}
			h.PublishChatMessage([]byte(msg.Payload))
		}
	}
}
```

---

## 7. chat-ws/cmd/server/main.go

```go
// chat-ws: WebSocket server for real-time chat.
// Connects with ?token=JWT (same SECRET_KEY as Python). Subscribes to Redis chat:conversation:* and forwards to connected clients.
package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"syscall"

	"linkup/chat-ws/internal/config"
	"linkup/chat-ws/internal/hub"
	"linkup/chat-ws/internal/redis"

	"github.com/redis/go-redis/v9"
)

func main() {
	cfg := config.LoadConfig()
	if cfg.SecretKey == "" {
		log.Fatal("SECRET_KEY (or JWT_SECRET) is required")
	}

	// Redis client for pub/sub and typing publish
	redisOpt, err := redis.ParseURL(cfg.RedisURL)
	if err != nil {
		log.Fatalf("redis parse URL: %v", err)
	}
	redisClient := redis.NewClient(redisOpt)
	defer redisClient.Close()

	h := hub.NewHub(redisClient)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go redis.RunSubscriber(ctx, cfg.RedisURL, h)

	http.HandleFunc("/ws", h.HandleWS(cfg))
	addr := ":" + strconv.Itoa(cfg.Port)
	log.Printf("chat-ws listening on %s (WebSocket: /ws?token=JWT)", addr)

	go func() {
		if err := http.ListenAndServe(addr, nil); err != nil && err != http.ErrServerClosed {
			log.Fatal(err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	log.Println("shutting down...")
	cancel()
}
```

---

## 8. frontend/src/config/env.ts

```ts
// בפיתוח: URL יחסי כדי שהבקשות יעברו דרך Vite proxy (ללא CORS). בפרודקשן: VITE_API_URL או fallback
const API_BASE_URL = import.meta.env.DEV
  ? '/api/v1'
  : (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1');

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

// timeout לבקשות API (מילישניות). ברירת מחדל 30 שניות – מונע timeout בהתחלה איטית של השרת
const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS) || 30000;

// WebSocket של שרת הצ'אט (chat-ws). בפיתוח: לפי VITE_CHAT_WS_URL או נגזר מ-API.
const CHAT_WS_URL = import.meta.env.VITE_CHAT_WS_URL
  || (import.meta.env.DEV ? 'ws://localhost:8081/ws' : (() => {
      const base = import.meta.env.VITE_API_URL || window.location.origin;
      const wsBase = base.replace(/^http/, 'ws').replace(/\/api\/v1\/?$/, '');
      return `${wsBase.replace(/\/$/, '')}:8081/ws`;
    })());

export { API_BASE_URL, GOOGLE_MAPS_API_KEY, API_TIMEOUT_MS, CHAT_WS_URL };
```

---

## 9. frontend/src/pages/MessageThread.tsx

```tsx
import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  getConversation,
  getMessages,
  sendMessage,
  type ConversationDetail,
  type MessageResponse,
} from '../api/client';
import { CHAT_WS_URL } from '../config/env';
import { formatDateTimeNoSeconds } from '../utils/date';
import styles from './MessageThread.module.css';

const TYPING_THROTTLE_MS = 4000;
const TYPING_DISPLAY_TIMEOUT_MS = 5000;

export default function MessageThread() {
  const { conversationId } = useParams<{ conversationId: string }>();
  const { user } = useAuth();
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const [input, setInput] = useState('');
  const [partnerTyping, setPartnerTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const typingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastTypingSentRef = useRef<number>(0);

  const cid = conversationId ?? '';

  const fetchConversation = useCallback(async () => {
    if (!cid || !user?.user_id) return;
    setLoading(true);
    setError('');
    try {
      const [convRes, msgRes] = await Promise.all([
        getConversation(cid),
        getMessages(cid, { limit: 100 }),
      ]);
      setConversation(convRes.data);
      setMessages(Array.isArray(msgRes.data) ? msgRes.data : []);
    } catch {
      setError('לא ניתן לטעון את השיחה');
    } finally {
      setLoading(false);
    }
  }, [cid, user?.user_id]);

  useEffect(() => {
    fetchConversation();
  }, [fetchConversation]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // WebSocket: חיבור ל-chat-ws כשנכנסים לשיחה ויש conversation + token
  useEffect(() => {
    if (!cid || !conversation || !user?.user_id) return;
    const token = localStorage.getItem('linkup_access_token');
    if (!token) return;
    const url = `${CHAT_WS_URL}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'typing_start') {
          setPartnerTyping(true);
          if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
          typingTimeoutRef.current = setTimeout(() => {
            setPartnerTyping(false);
            typingTimeoutRef.current = null;
          }, TYPING_DISPLAY_TIMEOUT_MS);
        }
        if (data.message_id != null && data.conversation_id === cid) {
          setMessages((prev) => {
            if (prev.some((m) => m.message_id === data.message_id)) return prev;
            return [...prev, { ...data, sender_id: data.sender_id, created_at: data.created_at }];
          });
        }
      } catch {
        // ignore parse errors
      }
    };
    ws.onclose = () => { wsRef.current = null; };
    return () => {
      if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
      ws.close();
      wsRef.current = null;
    };
  }, [cid, conversation, user?.user_id]);

  const sendTypingIfThrottled = useCallback(() => {
    if (!conversation?.partner?.user_id || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const now = Date.now();
    if (now - lastTypingSentRef.current < TYPING_THROTTLE_MS) return;
    lastTypingSentRef.current = now;
    const payload = JSON.stringify({
      type: 'typing_start',
      conversation_id: cid,
      recipient_id: conversation.partner.user_id,
    });
    wsRef.current.send(payload);
  }, [cid, conversation?.partner?.user_id]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const body = input.trim();
    if (!body || !cid || sending) return;
    setSending(true);
    setError('');
    try {
      const { data } = await sendMessage(cid, body);
      setMessages((prev) => [...prev, data]);
      setInput('');
    } catch {
      setError('שליחת ההודעה נכשלה');
    } finally {
      setSending(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    sendTypingIfThrottled();
  };

  if (loading) {
    return (
      <div className={styles.page}>
        <p className="page-loading">טוען שיחה...</p>
      </div>
    );
  }

  if (error && !conversation) {
    return (
      <div className={styles.page}>
        <p className={styles.pageError}>{error}</p>
        <Link to="/messages" className={`${styles.btn} ${styles.btnOutline}`} style={{ marginTop: '1rem' }}>
          חזרה להודעות
        </Link>
      </div>
    );
  }

  const partnerName = conversation?.partner?.full_name || (cid ? `שיחה` : '');

  return (
    <div className={styles.page} style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Link to="/messages" className={`${styles.btn} ${styles.btnOutline}`} style={{ fontSize: '0.875rem' }}>
          ← הודעות
        </Link>
        <h1 className={styles.pageTitle} style={{ margin: 0, flex: 1 }}>
          {partnerName}
        </h1>
      </div>
      {error && <p className={styles.pageError}>{error}</p>}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          border: '1px solid #e5e7eb',
          borderRadius: 8,
          padding: '1rem',
          minHeight: 200,
          maxHeight: 400,
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
        }}
      >
        {messages.length === 0 ? (
          <p className={styles.emptyText} style={{ margin: 'auto' }}>
            אין הודעות. שלח הודעה ראשונה.
          </p>
        ) : (
          messages.map((m) => {
            const isMe = m.sender_id === user?.user_id;
            return (
              <div
                key={m.message_id}
                style={{
                  alignSelf: isMe ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  padding: '0.5rem 0.75rem',
                  borderRadius: 8,
                  background: isMe ? 'var(--primary, #2563eb)' : 'var(--surface, #f3f4f6)',
                  color: isMe ? '#fff' : 'inherit',
                }}
              >
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{m.body}</div>
                <div
                  style={{
                    fontSize: '0.75rem',
                    opacity: 0.85,
                    marginTop: '0.25rem',
                  }}
                >
                  {formatDateTimeNoSeconds(m.created_at)}
                </div>
              </div>
            );
          })
        )}
        {partnerTyping && (
          <p style={{ fontSize: '0.875rem', color: 'var(--muted)', margin: '0.25rem 0 0' }}>
            {partnerName} מקליד...
          </p>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSend} style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          placeholder="כתוב הודעה..."
          className={styles.formInput}
          style={{ flex: 1 }}
          maxLength={10000}
        />
        <button type="submit" className={`${styles.btn} ${styles.btnSuccess}`} disabled={sending || !input.trim()}>
          {sending ? '...' : 'שלח'}
        </button>
      </form>
    </div>
  );
}
```

---

**סוף המסמך.**  
לשמירה כ-DOC: פתח את הקובץ ב-Word (קובץ → פתח → בחר את הקובץ .md) ואז "שמור בשם" → Word Document (.docx).
