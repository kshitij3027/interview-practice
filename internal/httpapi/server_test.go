package httpapi

import (
 "encoding/json"
 "net/http"
 "net/http/httptest"
 "strings"
 "testing"
 "casefold/internal/workspace"
)
func handler(t *testing.T)http.Handler{t.Helper();s,e:=workspace.New(workspace.Seed{Organizations:[]workspace.Organization{{ID:"a",Name:"A"},{ID:"b",Name:"B"}},Customers:[]workspace.Customer{{ID:"ca",OrgID:"a",Name:"A"},{ID:"cb",OrgID:"b",Name:"B"}},Cases:[]workspace.Case{{ID:"Z1",OrgID:"a",CustomerID:"ca",Subject:"Help",Status:"open",Priority:"low",Revision:1},{ID:"Z2",OrgID:"b",CustomerID:"cb",Subject:"Secret",Status:"open",Priority:"low",Revision:1}}});if e!=nil{t.Fatal(e)};return New(s)}
func TestListAndPrivacy(t *testing.T){h:=handler(t);r:=httptest.NewRecorder();h.ServeHTTP(r,httptest.NewRequest("GET","/api/cases?org=a&status=all",nil));if r.Code!=200{t.Fatal(r.Code,r.Body)};var got workspace.ListResult;if e:=json.Unmarshal(r.Body.Bytes(),&got);e!=nil{t.Fatal(e)};if got.Total!=1||got.Cases[0].ID!="Z1"{t.Fatalf("unexpected result: %+v",got)};r=httptest.NewRecorder();h.ServeHTTP(r,httptest.NewRequest("GET","/api/cases/Z2?org=a",nil));if r.Code!=404{t.Fatalf("cross org %d",r.Code)}}
func TestNoteMutationAndConflict(t *testing.T){h:=handler(t);b:=`{"orgId":"a","expectedRevision":1,"note":" hello "}`;r:=httptest.NewRecorder();h.ServeHTTP(r,httptest.NewRequest("POST","/api/cases/Z1/note",strings.NewReader(b)));if r.Code!=200||!strings.Contains(r.Body.String(),`"revision":2`){t.Fatal(r.Code,r.Body)};r=httptest.NewRecorder();h.ServeHTTP(r,httptest.NewRequest("POST","/api/cases/Z1/note",strings.NewReader(b)));if r.Code!=409||!strings.Contains(r.Body.String(),`"current"`){t.Fatal(r.Code,r.Body)}}
func TestInvalidPagination(t *testing.T){h:=handler(t);r:=httptest.NewRecorder();h.ServeHTTP(r,httptest.NewRequest("GET","/api/cases?org=a&limit=101",nil));if r.Code!=400{t.Fatalf("expected 400 got %d",r.Code)}}
