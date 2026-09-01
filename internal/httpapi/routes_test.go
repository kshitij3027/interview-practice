package httpapi

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"interview-practice/customermerge/internal/service"
	"interview-practice/customermerge/internal/store"
)

func testHandler(t *testing.T) http.Handler {
	t.Helper()
	s, err := store.Load("../../fixtures/customers.json")
	if err != nil {
		t.Fatal(err)
	}
	return New(service.NewCustomerService(s)).Handler()
}

func TestCustomerListEndpoint(t *testing.T) {
	h := testHandler(t)
	req := httptest.NewRequest(http.MethodGet, "/api/customers?segment=midmarket", nil)
	res := httptest.NewRecorder()
	h.ServeHTTP(res, req)
	if res.Code != 200 {
		t.Fatalf("code=%d body=%s", res.Code, res.Body.String())
	}
	var payload map[string]any
	if err := json.Unmarshal(res.Body.Bytes(), &payload); err != nil {
		t.Fatal(err)
	}
	if got := len(payload["customers"].([]any)); got != 2 {
		t.Fatalf("customers=%d", got)
	}
}

func TestStaleStatusReturnsConflict(t *testing.T) {
	h := testHandler(t)
	body := bytes.NewBufferString(`{"status":"paused","expected_revision":99}`)
	req := httptest.NewRequest(http.MethodPatch, "/api/customers/cus_1001/status", body)
	res := httptest.NewRecorder()
	h.ServeHTTP(res, req)
	if res.Code != 409 {
		t.Fatalf("code=%d body=%s", res.Code, res.Body.String())
	}
}
