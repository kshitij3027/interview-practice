package httpapi

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"queuepilot/internal/service"
	"queuepilot/internal/store"
)

func handler(t *testing.T) http.Handler { t.Helper(); s,err:=store.New("../../fixtures/rep_roster.json"); if err!=nil{t.Fatal(err)}; return API{Service:service.OpportunityService{Store:s}}.Handler() }
func TestListEndpoint(t *testing.T){rr:=httptest.NewRecorder();req:=httptest.NewRequest("GET","/api/opportunities?limit=2",nil);handler(t).ServeHTTP(rr,req);if rr.Code!=200{t.Fatalf("status %d",rr.Code)};var body map[string]any;if json.Unmarshal(rr.Body.Bytes(),&body)!=nil{t.Fatal("bad json")};if len(body["items"].([]any))!=2{t.Fatal("expected two items")}}
func TestSingleReassignWorks(t *testing.T){rr:=httptest.NewRecorder();req:=httptest.NewRequest("POST","/api/opportunities/opp-104/reassign",bytes.NewBufferString(`{"target_owner_id":"rep-ben","expected_revision":2}`));handler(t).ServeHTTP(rr,req);if rr.Code!=200{t.Fatalf("status %d: %s",rr.Code,rr.Body.String())}}
func TestSingleReassignRejectsStaleRevision(t *testing.T){rr:=httptest.NewRecorder();req:=httptest.NewRequest("POST","/api/opportunities/opp-101/reassign",bytes.NewBufferString(`{"target_owner_id":"rep-cam","expected_revision":99}`));handler(t).ServeHTTP(rr,req);if rr.Code!=409{t.Fatalf("status %d",rr.Code)}}
func TestSingleReassignEnforcesRegion(t *testing.T){rr:=httptest.NewRecorder();req:=httptest.NewRequest("POST","/api/opportunities/opp-102/reassign",bytes.NewBufferString(`{"target_owner_id":"rep-ava","expected_revision":3}`));handler(t).ServeHTTP(rr,req);if rr.Code!=409{t.Fatalf("status %d",rr.Code)}}
