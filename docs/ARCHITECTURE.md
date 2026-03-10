# Linkup — Architecture Overview

## Services

| Service        | Path        | Language        | Port | Purpose                          |
|----------------|-------------|-----------------|------|----------------------------------|
| linkup-api     | backend/    | Python / FastAPI| 8000 | REST API, auth, rides, bookings  |
| linkup-chat-ws | chat-ws/    | Go              | 8081 | WebSocket server for real-time chat |
| linkup-web     | frontend/   | React / TypeScript | 5173 | Web client                    |
| linkup-mobile  | mobile/     | React Native / Expo | —  | Mobile client                  |

## Communication

- Clients → linkup-api: REST HTTP
- Clients → linkup-chat-ws: WebSocket
- linkup-chat-ws ↔ Redis: Pub/Sub for message routing
- linkup-api → Redis: Publish chat messages and chat completion events (DB 1)
- linkup-api → RabbitMQ: Event publishing via Outbox pattern
- Backend worker: Listens to Redis DB 1 for chat completion, runs AI analysis (Groq), saves to DB and outbox

## Key Patterns

- **Outbox Pattern**: events written to DB first,
  worker publishes to RabbitMQ asynchronously
- **Domain-Driven Design**: each domain owns
  model, schema, crud, service
- **JWT Auth**: shared secret between backend
  and chat-ws for WebSocket authentication

## Future Considerations

- **Kafka**: Kafka was considered for high-throughput event streaming but removed in favor of RabbitMQ for simplicity at current scale.
