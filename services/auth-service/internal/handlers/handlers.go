package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/rs/zerolog/log"
)

// HealthResponse simple health payload
type HealthResponse struct {
	Status string `json:"status"`
}

// RegisterRoutes registers public HTTP routes used by platform components and clients.
func RegisterRoutes(mux *http.ServeMux) {
	mux.HandleFunc("/api/v1/health", healthHandler)
	mux.HandleFunc("/api/v1/ready", readyHandler)
	mux.HandleFunc("/api/v1/auth/login", loginHandler)
	mux.HandleFunc("/api/v1/auth/refresh", refreshHandler)
	mux.HandleFunc("/api/v1/auth/logout", logoutHandler)
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	resp := HealthResponse{Status: "ok"}
	writeJSON(w, http.StatusOK, resp)
}

func readyHandler(w http.ResponseWriter, r *http.Request) {
	// In a full implementation this would check DB and Redis connectivity.
	resp := HealthResponse{Status: "ready"}
	writeJSON(w, http.StatusOK, resp)
}

func loginHandler(w http.ResponseWriter, r *http.Request) {
	// Minimal stub: parse credentials and return 401. Implement real auth logic in storage/auth.
	var req map[string]string
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		log.Warn().Err(err).Msg("invalid login payload")
		http.Error(w, "invalid payload", http.StatusBadRequest)
		return
	}
	email := req["email"]
	pass := req["password"]
	if email == "" || pass == "" {
		http.Error(w, "missing credentials", http.StatusBadRequest)
		return
	}
	// For now return 401 to indicate credentials required to be validated by concrete logic.
	http.Error(w, "invalid credentials", http.StatusUnauthorized)
}

func refreshHandler(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "not implemented", http.StatusNotImplemented)
}

func logoutHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
