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
