package hub

// ChatMessage is the payload we send over WS (same as Redis payload from Python).
type ChatMessage struct {
	MessageID      int    `json:"message_id"`
	ConversationID int    `json:"conversation_id"`
	SenderID       int    `json:"sender_id"`
	RecipientID    int    `json:"recipient_id"`
	Body           string `json:"body"`
	CreatedAt      string `json:"created_at"`
}
