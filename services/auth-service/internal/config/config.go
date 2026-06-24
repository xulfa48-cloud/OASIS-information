package config

import (
	"errors"
	"os"
	"strconv"
	"time"
)

// Config holds runtime configuration for the auth-service.
type Config struct {
	Port           string
	Env            string
	DatabaseURL    string
	RedisURL       string
	JWTPrivateKey  string
	JWTIssuer      string
	JWTExpSeconds  int
	LogLevel       string
	KafkaBrokers   []string
	MetricsAddress string
	ReadyTimeout   time.Duration
}

// LoadFromEnv reads configuration from environment variables and returns a validated Config.
func LoadFromEnv() (*Config, error) {
	c := &Config{}

	c.Port = getenvDefault("AUTH_PORT", "8080")
	c.Env = getenvDefault("AUTH_ENV", "development")
	c.DatabaseURL = os.Getenv("AUTH_DATABASE_URL")
	c.RedisURL = os.Getenv("AUTH_REDIS_URL")
	c.JWTPrivateKey = os.Getenv("AUTH_JWT_PRIVATE_KEY")
	c.JWTIssuer = getenvDefault("AUTH_JWT_ISSUER", "oasis-auth")
	
	expStr := getenvDefault("AUTH_JWT_EXP_SECONDS", "3600")
	exp, err := strconv.Atoi(expStr)
	if err != nil {
		return nil, err
	}
	c.JWTExpSeconds = exp

	c.LogLevel = getenvDefault("AUTH_LOG_LEVEL", "info")

	kafka := os.Getenv("AUTH_KAFKA_BROKERS")
	if kafka != "" {
		c.KafkaBrokers = splitAndTrim(kafka, ",")
	}

	c.MetricsAddress = getenvDefault("AUTH_METRICS_ADDRESS", ":9090")
	c.ReadyTimeout = 10 * time.Second

	// Basic validation
	if c.DatabaseURL == "" {
		return nil, errors.New("AUTH_DATABASE_URL is required")
	}
	if c.JWTPrivateKey == "" {
		return nil, errors.New("AUTH_JWT_PRIVATE_KEY is required")
	}

	return c, nil
}

func getenvDefault(k, d string) string {
	v := os.Getenv(k)
	if v == "" {
		return d
	}
	return v
}

func splitAndTrim(s, sep string) []string {
	var out []string
	for _, p := range splitNonEmpty(s, sep) {
		out = append(out, p)
	}
	return out
}

func splitNonEmpty(s, sep string) []string {
	var res []string
	for _, p := range split(s, sep) {
		if p != "" {
			res = append(res, p)
		}
	}
	return res
}

func split(s, sep string) []string {
	// avoid importing strings for trivial split
	var res []string
	cur := ""
	for i := 0; i < len(s); i++ {
		c := s[i]
		if string(c) == sep {
			res = append(res, cur)
			cur = ""
			continue
		}
		cur += string(c)
	}
	res = append(res, cur)
	return res
}
