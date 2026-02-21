# Dockerfile for Go WebSocket server
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go.mod first
COPY go.mod ./
RUN go mod download

# Copy source code
COPY . .

# Run go mod tidy AFTER copying source code to ensure go.sum is correct
# This will create/update go.sum based on the actual imports in the code
RUN go mod tidy

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o /app/chat-ws ./cmd/server

# Final stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /root/

COPY --from=builder /app/chat-ws .

EXPOSE 8081

CMD ["./chat-ws"]
