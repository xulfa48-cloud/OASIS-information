package server

import (
	"context"
	"net/http"
	"time"

	"github.com/rs/zerolog/log"
	"github.com/xulfa48-cloud/OASIS-information/services/auth-service/internal/config"
)

// New returns a configured http.Server with basic routes registered.
func New(cfg *config.Config, handler http.Handler) *http.Server {
	addr := ":" + cfg.Port
	if cfg.Port[0] == ':' {
		addr = cfg.Port
	}

	srv := &http.Server{
		Addr:         addr,
		Handler:      handler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 20 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	log.Info().Str("addr", addr).Msg("auth-service server configured")
	return srv
}

// GracefulShutdown attempts to shutdown the server with a timeout.
func GracefulShutdown(srv *http.Server, timeout time.Duration) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Error().Err(err).Msg("server graceful shutdown failed")
	}
}
