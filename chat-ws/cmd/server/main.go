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
)

func main() {
	cfg := config.LoadConfig()
	if cfg.SecretKey == "" {
		log.Fatal("SECRET_KEY (or JWT_SECRET) is required")
	}

	h := hub.NewHub()
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
