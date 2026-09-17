package api

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"interview-practice/returnscan/internal/model"
	"interview-practice/returnscan/internal/store"
)

func testServer() *Server {
	c := model.ReturnCase{ID: "RET-1", OrderID: "ORD-1", Warehouse: "SFO", CreatedAt: time.Now(), ExpectedParcels: []string{"PKG-1"}, Status: "awaiting", Revision: 1}
	return New(store.New([]model.ReturnCase{c}), []string{"B-1", "B-2"})
}

func TestListAndConfig(t *testing.T) {
	h := testServer().Handler()
	r := httptest.NewRequest("GET", "/api/config", nil)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 200 {
		t.Fatalf("config status %d", w.Code)
	}
	r = httptest.NewRequest("GET", "/api/returns?warehouse=SFO&status=awaiting", nil)
	w = httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 200 {
		t.Fatalf("list status %d", w.Code)
	}
	var body map[string]any
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
}

func TestExceptionStaleReturnsCurrentState(t *testing.T) {
	h := testServer().Handler()
	body := bytes.NewBufferString(`{"expected_revision":9,"active":true,"reason":"damage"}`)
	r := httptest.NewRequest("PUT", "/api/returns/RET-1/exception", body)
	r.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != http.StatusConflict {
		t.Fatalf("expected 409, got %d: %s", w.Code, w.Body.String())
	}
}
