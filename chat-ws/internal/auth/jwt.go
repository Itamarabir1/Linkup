package auth

import (
	"fmt"
	"strconv"

	"github.com/golang-jwt/jwt/v5"
)

// Claims for access token (same structure as Python: sub = user_id).
type claims struct {
	Sub string `json:"sub"`
	jwt.RegisteredClaims
}

// ValidateToken parses the JWT and returns user_id (sub) as int. Same SECRET_KEY and algorithm as Python.
func ValidateToken(tokenString, secretKey, alg string) (userID int, err error) {
	if secretKey == "" {
		return 0, fmt.Errorf("SECRET_KEY is required")
	}
	token, err := jwt.ParseWithClaims(tokenString, &claims{}, func(t *jwt.Token) (interface{}, error) {
		if t.Method.Alg() != alg {
			return nil, fmt.Errorf("unexpected alg: %s", t.Method.Alg())
		}
		return []byte(secretKey), nil
	})
	if err != nil {
		return 0, err
	}
	c, ok := token.Claims.(*claims)
	if !ok || !token.Valid {
		return 0, fmt.Errorf("invalid token")
	}
	userID, err = strconv.Atoi(c.Sub)
	if err != nil {
		return 0, fmt.Errorf("invalid sub: %s", c.Sub)
	}
	return userID, nil
}
