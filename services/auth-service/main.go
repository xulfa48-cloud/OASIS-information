package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/joho/godotenv"

	"github.com/researchos/services/auth-service/internal/config"
	"github.com/researchos/services/auth-service/internal/handler"
	"github.com/researchos/services/auth-service/internal/repository"
	"github.com/researchos/services/auth-service/internal/service"
)

func main() {
	// Load environment
	godotenv.Load()

	// Load config
	cfg := config.Load()

	// Initialize database
	db, err := repository.Connect(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close(context.Background())

	// Initialize repositories
	userRepo := repository.NewUserRepository(db)
	sessionRepo := repository.NewSessionRepository(db)
	oauthRepo := repository.NewOAuthRepository(db)
	mfaRepo := repository.NewMFARepository(db)

	// Initialize services
	authSvc := service.NewAuthService(userRepo, sessionRepo, cfg)
	oauthSvc := service.NewOAuthService(oauthRepo, cfg)
	mfaSvc := service.NewMFAService(mfaRepo, cfg)

	// Initialize handlers
	authHandler := handler.NewAuthHandler(authSvc, oauthSvc, mfaSvc)

	// Setup router
	router := chi.NewRouter()
	router.Use(middleware.Logger)
	router.Use(middleware.Recoverer)

	// Register routes
	authHandler.RegisterRoutes(router)

	// Start server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Port),
		Handler: router,
	}

	go func() {
		log.Printf("Auth service listening on %s", server.Addr)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server error: %v", err)
		}
	}()

	// Graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
	<-sigChan

	log.Println("Shutting down...")
	server.Shutdown(context.Background())
}
