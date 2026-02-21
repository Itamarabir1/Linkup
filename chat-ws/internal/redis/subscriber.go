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
