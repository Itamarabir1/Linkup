package hub

import (
	"context"
	"encoding/json"
	"log"
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

// PublishTyping publishes a typing event to Redis channel chat:typing:{conversationID}. No-op if redisClient is nil.
func (h *Hub) PublishTyping(ctx context.Context, conversationID string, payload []byte) {
	if h.redisClient == nil {
		return
	}
	channel := "chat:typing:" + conversationID
	if err := h.redisClient.Publish(ctx, channel, payload).Err(); err != nil {
		return // log optional
	}
}

// PublishTypingMessage is called when we receive a typing event from Redis; payload is JSON. Sends to recipient.
func (h *Hub) PublishTypingMessage(payload []byte) {
	var msg TypingPayload
	if err := json.Unmarshal(payload, &msg); err != nil {
		log.Printf("redis typing payload unmarshal: %v", err)
		return
	}
	h.SendToUser(msg.RecipientID, payload)
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
