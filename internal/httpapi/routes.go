package httpapi

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"

	"interview-practice/customermerge/internal/service"
	"interview-practice/customermerge/internal/store"
)

type API struct {
	service *service.CustomerService
}

func New(s *service.CustomerService) *API { return &API{service: s} }

func (a *API) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/health", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, map[string]any{"ok": true}) })
	mux.HandleFunc("GET /api/customers", a.listCustomers)
	mux.HandleFunc("GET /api/customers/{id}", a.getCustomer)
	mux.HandleFunc("PATCH /api/customers/{id}/status", a.setStatus)
	mux.Handle("/", http.FileServer(http.Dir("web")))
	return mux
}

func (a *API) listCustomers(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, a.service.List(r.URL.Query().Get("segment")))
}

func (a *API) getCustomer(w http.ResponseWriter, r *http.Request) {
	result, err := a.service.Detail(r.PathValue("id"))
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, 200, result)
}

type statusRequest struct {
	Status           string `json:"status"`
	ExpectedRevision int    `json:"expected_revision"`
}

func (a *API) setStatus(w http.ResponseWriter, r *http.Request) {
	var req statusRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, 400, map[string]string{"error": "invalid JSON body"})
		return
	}
	result, err := a.service.SetStatus(r.PathValue("id"), req.Status, req.ExpectedRevision)
	if err != nil {
		writeError(w, err)
		return
	}
	writeJSON(w, 200, result)
}

func writeError(w http.ResponseWriter, err error) {
	switch {
	case errors.Is(err, store.ErrNotFound):
		writeJSON(w, 404, map[string]string{"error": err.Error()})
	case errors.Is(err, store.ErrStaleRevision):
		writeJSON(w, 409, map[string]string{"error": err.Error()})
	case errors.Is(err, store.ErrInvalidStatus):
		writeJSON(w, 422, map[string]string{"error": err.Error()})
	default:
		writeJSON(w, 500, map[string]string{"error": "internal error"})
	}
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}

func IntQuery(r *http.Request, key string, fallback int) int {
	value := strings.TrimSpace(r.URL.Query().Get(key))
	if value == "" {
		return fallback
	}
	n, err := strconv.Atoi(value)
	if err != nil {
		return fallback
	}
	return n
}
