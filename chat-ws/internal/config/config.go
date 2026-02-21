package config

import (
	"os"
	"strconv"
)

// Config holds env-based configuration. Same SECRET_KEY and REDIS_URL as Python backend.
type Config struct {
	Port       int    // WS server port (default 8081)
	RedisURL   string // e.g. redis://localhost:6379/0
	SecretKey  string // JWT secret (same as Python SECRET_KEY)
	JWTAlg     string // HS256
}

func LoadConfig() Config {
	port := 8081
	if p := os.Getenv("PORT"); p != "" {
		if v, err := strconv.Atoi(p); err == nil {
			port = v
		}
	}
	redisURL := os.Getenv("REDIS_URL")
	if redisURL == "" {
		redisURL = "redis://localhost:6379/0"
	}
	secret := os.Getenv("SECRET_KEY")
	if secret == "" {
		secret = os.Getenv("JWT_SECRET")
	}
	alg := os.Getenv("JWT_ALGORITHM")
	if alg == "" {
		alg = "HS256"
	}
	return Config{
		Port:      port,
		RedisURL:  redisURL,
		SecretKey: secret,
		JWTAlg:    alg,
	}
}
