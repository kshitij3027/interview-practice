package httpapi

import (
 "encoding/json"
 "errors"
 "io"
 "net/http"
 "strconv"
 "strings"
 "casefold/internal/workspace"
)

type Server struct { Store *workspace.Store }
func New(store *workspace.Store) http.Handler {s:=&Server{Store:store};return s.routes()}
func (s *Server) routes() http.Handler {
 mux:=http.NewServeMux()
 mux.HandleFunc("GET /api/health",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,map[string]string{"status":"ok"})})
 mux.HandleFunc("GET /api/organizations",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,s.Store.Organizations())})
 mux.HandleFunc("GET /api/customers",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,s.Store.Customers(r.URL.Query().Get("org")))})
 mux.HandleFunc("GET /api/cases",s.list)
 mux.HandleFunc("GET /api/cases/{id}",s.detail)
 mux.HandleFunc("POST /api/cases/{id}/note",s.note)
 mux.Handle("/",http.FileServer(http.Dir("web")))
 return mux
}
func writeJSON(w http.ResponseWriter,code int,v any){w.Header().Set("Content-Type","application/json; charset=utf-8");w.WriteHeader(code);_ = json.NewEncoder(w).Encode(v)}
func fail(w http.ResponseWriter,e error){var f *workspace.Fault;if errors.As(e,&f){v:=map[string]any{"error":f.Message};if f.Current!=nil{v["current"]=f.Current};writeJSON(w,f.Code,v)}else{writeJSON(w,500,map[string]string{"error":"unexpected server error"})}}
func pageNum(raw string,def int)(int,error){if raw==""{return def,nil};n,e:=strconv.Atoi(raw);if e!=nil {return 0,workspace.Bad("invalid pagination")};return n,nil}
func (s *Server) list(w http.ResponseWriter,r *http.Request){
 q:=r.URL.Query();offset,e:=pageNum(q.Get("offset"),0);if e!=nil{fail(w,e);return};limit,e:=pageNum(q.Get("limit"),20);if e!=nil{fail(w,e);return}
 status:=q.Get("status");if status==""{status="all"}
 result,e:=s.Store.List(q.Get("org"),q.Get("q"),status,offset,limit);if e!=nil{fail(w,e);return};writeJSON(w,200,result)
}
func (s *Server) detail(w http.ResponseWriter,r *http.Request){c,e:=s.Store.Detail(r.URL.Query().Get("org"),r.PathValue("id"));if e!=nil{fail(w,e);return};writeJSON(w,200,c)}
func (s *Server) note(w http.ResponseWriter,r *http.Request){
 var b struct {OrgID string `json:"orgId"`;ExpectedRevision *int `json:"expectedRevision"`;Note *string `json:"note"`}
 r.Body=http.MaxBytesReader(w,r.Body,64<<10)
 dec:=json.NewDecoder(r.Body);dec.DisallowUnknownFields();if err:=dec.Decode(&b);err!=nil{fail(w,workspace.Bad("invalid JSON body"));return}
 var extra any;if dec.Decode(&extra)!=io.EOF{fail(w,workspace.Bad("unexpected trailing JSON"));return}
 if b.OrgID==""||b.ExpectedRevision==nil||b.Note==nil||strings.TrimSpace(b.OrgID)!=b.OrgID{fail(w,workspace.Bad("missing note fields"));return}
 c,e:=s.Store.UpdateNote(b.OrgID,r.PathValue("id"),*b.ExpectedRevision,*b.Note);if e!=nil{fail(w,e);return};writeJSON(w,200,c)
}
