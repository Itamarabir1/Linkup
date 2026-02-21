package hub

import "sync"

// Hub maps user_id -> list of connections (one user can have multiple devices).
type Hub struct {
	mu    sync.RWMutex
	users map[int][]*Conn
}

func NewHub() *Hub {
	return &Hub{users: make(map[int][]*Conn)}
}

// Register adds a connection for userID.
func (h *Hub) Register(userID int, c *Conn) {
	h.mu.Lock()
	defer h.mu.Unlock()
	h.users[userID] = append(h.users[userID], c)
}

// Unregister removes a connection.
func (h *Hub) Unregister(userID int, c *Conn) {
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
func (h *Hub) SendToUser(userID int, payload []byte) {
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
