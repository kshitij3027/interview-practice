package api

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"

	"interview-practice/returnscan/internal/store"
)

type Server struct {
	store    *store.Store
	batchIDs []string
}

func New(s *store.Store, batchIDs []string) *Server {
	return &Server{store: s, batchIDs: append([]string(nil), batchIDs...)}
}

func (s *Server) Handler() http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/health", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, map[string]any{"ok": true}) })
	mux.HandleFunc("GET /api/config", func(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, map[string]any{"batch_ids": s.batchIDs}) })
	mux.HandleFunc("GET /api/returns", s.listReturns)
	mux.HandleFunc("GET /api/returns/{id}", s.getReturn)
	mux.HandleFunc("PUT /api/returns/{id}/exception", s.setException)
	return mux
}

func (s *Server) listReturns(w http.ResponseWriter, r *http.Request) {
	warehouse := strings.TrimSpace(r.URL.Query().Get("warehouse"))
	status := strings.TrimSpace(r.URL.Query().Get("status"))
	if status != "" && status != "awaiting" && status != "partial" && status != "received" {
		writeError(w, 400, "invalid status")
		return
	}
	writeJSON(w, 200, s.store.Snapshot(warehouse, status))
}

func (s *Server) getReturn(w http.ResponseWriter, r *http.Request) {
	c, rev, err := s.store.Get(r.PathValue("id"))
	if err != nil {
		writeError(w, 404, "return not found")
		return
	}
	writeJSON(w, 200, map[string]any{"case": c, "dataset_revision": rev})
}

type exceptionRequest struct {
	ExpectedRevision int    `json:"expected_revision"`
	Active           bool   `json:"active"`
	Reason           string `json:"reason"`
}

func (s *Server) setException(w http.ResponseWriter, r *http.Request) {
	var req exceptionRequest
	dec := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		writeError(w, 400, "invalid JSON body")
		return
	}
	if req.ExpectedRevision < 1 {
		writeError(w, 400, "expected_revision must be positive")
		return
	}
	c, datasetRev, changed, err := s.store.SetException(r.PathValue("id"), req.ExpectedRevision, req.Active, req.Reason)
	if errors.Is(err, store.ErrNotFound) {
		writeError(w, 404, "return not found")
		return
	}
	if errors.Is(err, store.ErrInvalidReason) {
		writeError(w, 400, err.Error())
		return
	}
	if errors.Is(err, store.ErrStale) {
		writeJSON(w, 409, map[string]any{"error": "stale revision", "case": c, "dataset_revision": datasetRev})
		return
	}
	writeJSON(w, 200, map[string]any{"case": c, "dataset_revision": datasetRev, "changed": changed})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}
func writeError(w http.ResponseWriter, status int, msg string) {
	writeJSON(w, status, map[string]any{"error": msg})
}

func ParseDelayMS(raw string, max int) (int, error) {
	if raw == "" {
		return 0, nil
	}
	n, err := strconv.Atoi(raw)
	if err != nil || n < 0 || n > max {
		return 0, errors.New("invalid delay_ms")
	}
	return n, nil
}
