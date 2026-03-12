package redis

import (
	"context"
	"strings"

	"github.com/redis/go-redis/v9"

	"linkup/chat-ws/internal/hub"
)

const (
	ChatChannelPattern   = "chat:conversation:*"
	TypingChannelPattern = "chat:typing:*"
)

// RunSubscriber subscribes to chat:conversation:* and chat:typing:* and forwards messages to the Hub.
// Caller owns the client; RunSubscriber does not close it.
func RunSubscriber(ctx context.Context, client *redis.Client, h *hub.Hub) {
	pubsub := client.PSubscribe(ctx, ChatChannelPattern, TypingChannelPattern)
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
			payload := []byte(msg.Payload)
			if strings.HasPrefix(msg.Channel, "chat:typing:") {
				h.PublishTypingMessage(payload)
			} else {
				h.PublishChatMessage(payload)
			}
		}
	}
}
