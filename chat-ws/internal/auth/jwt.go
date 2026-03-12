package auth

import (
	"fmt"

	"github.com/golang-jwt/jwt/v5"
)

// Claims for access token (same structure as Python: sub = user_id, UUID string).
type claims struct {
	Sub string `json:"sub"`
	jwt.RegisteredClaims
}

// ValidateToken parses the JWT and returns user_id (sub) as string. Supports UUID from Python backend.
func ValidateToken(tokenString, secretKey, alg string) (userID string, err error) {
	if secretKey == "" {
		return "", fmt.Errorf("SECRET_KEY is required")
	}
	token, err := jwt.ParseWithClaims(tokenString, &claims{}, func(t *jwt.Token) (interface{}, error) {
		if t.Method.Alg() != alg {
			return nil, fmt.Errorf("unexpected alg: %s", t.Method.Alg())
		}
		return []byte(secretKey), nil
	})
	if err != nil {
		return "", err
	}
	c, ok := token.Claims.(*claims)
	if !ok || !token.Valid {
		return "", fmt.Errorf("invalid token")
	}
	if c.Sub == "" {
		return "", fmt.Errorf("empty sub")
	}
	return c.Sub, nil
}
