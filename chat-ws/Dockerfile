# Build stage
FROM golang:1.21-alpine AS builder
WORKDIR /app

# Copy go.mod first (needed for module resolution)
COPY go.mod ./
RUN go mod download

# Copy source code directories (preserving module structure)
COPY cmd/ ./cmd/
COPY internal/ ./internal/

# Build the application
# Module name is "linkup/chat-ws", main.go is in cmd/server/
# The build command looks for main.go in ./cmd/server/ directory
RUN CGO_ENABLED=0 GOOS=linux go build -o /chat-ws ./cmd/server

# Run stage
FROM alpine:3.19
RUN apk --no-cache add ca-certificates
WORKDIR /app
COPY --from=builder /chat-ws .
EXPOSE 8081
CMD ["./chat-ws"]
