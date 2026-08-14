package httpapi

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"queuepilot/internal/service"
)

type API struct{ Service service.OpportunityService }
type reassignRequest struct { TargetOwnerID string `json:"target_owner_id"`; ExpectedRevision int `json:"expected_revision"` }
func (a API) Handler() http.Handler { mux:=http.NewServeMux(); mux.HandleFunc("/api/opportunities",a.list); mux.HandleFunc("/api/opportunities/",a.opportunityAction); mux.HandleFunc("/api/reps",a.reps); return withCORS(mux) }
func (a API) list(w http.ResponseWriter,r *http.Request){if r.Method!=http.MethodGet{writeError(w,405,"method_not_allowed");return};limit,_:=strconv.Atoi(r.URL.Query().Get("limit"));page:=a.Service.List(service.ListFilter{Owner:r.URL.Query().Get("owner"),Stage:r.URL.Query().Get("stage"),Query:r.URL.Query().Get("q"),Cursor:r.URL.Query().Get("cursor"),Limit:limit});writeJSON(w,200,page)}
func (a API) reps(w http.ResponseWriter,r *http.Request){if r.Method!=http.MethodGet{writeError(w,405,"method_not_allowed");return};writeJSON(w,200,a.Service.Reps())}
func (a API) opportunityAction(w http.ResponseWriter,r *http.Request){parts:=strings.Split(strings.TrimPrefix(r.URL.Path,"/api/opportunities/"),"/");if len(parts)!=2||parts[1]!="reassign"||r.Method!=http.MethodPost{writeError(w,404,"not_found");return};var req reassignRequest;if json.NewDecoder(r.Body).Decode(&req)!=nil||strings.TrimSpace(req.TargetOwnerID)==""||req.ExpectedRevision<=0{writeError(w,400,"invalid_request");return};o,err:=a.Service.Reassign(parts[0],req.TargetOwnerID,req.ExpectedRevision);if err!=nil{code:=409;if err.Error()=="not_found"||err.Error()=="rep_not_found"{code=404};writeError(w,code,err.Error());return};writeJSON(w,200,o)}
func writeJSON(w http.ResponseWriter,code int,v any){w.Header().Set("Content-Type","application/json");w.WriteHeader(code);_=json.NewEncoder(w).Encode(v)}
func writeError(w http.ResponseWriter,code int,msg string){writeJSON(w,code,map[string]string{"error":msg})}
func withCORS(next http.Handler) http.Handler{return http.HandlerFunc(func(w http.ResponseWriter,r *http.Request){w.Header().Set("Access-Control-Allow-Origin","*");w.Header().Set("Access-Control-Allow-Headers","Content-Type");if r.Method==http.MethodOptions{w.WriteHeader(204);return};next.ServeHTTP(w,r)})}
