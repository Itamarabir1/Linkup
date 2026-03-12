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
