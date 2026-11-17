package workspace

import (
 "encoding/json"
 "fmt"
 "os"
 "sort"
 "strings"
 "sync"
)

type Organization struct { ID string `json:"id"`; Name string `json:"name"` }
type Customer struct { ID string `json:"id"`; OrgID string `json:"orgId"`; Name string `json:"name"` }
type Entry struct { ID string `json:"id"`; At string `json:"at"`; Actor string `json:"actor"`; Text string `json:"text"` }
type Case struct {
 ID string `json:"id"`; OrgID string `json:"orgId"`; CustomerID string `json:"customerId"`
 Subject string `json:"subject"`; Status string `json:"status"`; Priority string `json:"priority"`
 Tags []string `json:"tags"`; Revision int `json:"revision"`; Note string `json:"note"`
 Timeline []Entry `json:"timeline"`
}
type Seed struct { Organizations []Organization `json:"organizations"`; Customers []Customer `json:"customers"`; Cases []Case `json:"cases"` }
type Store struct { mu sync.Mutex; orgs []Organization; customers []Customer; cases map[string]*Case }
type ListResult struct { Cases []Case `json:"cases"`; Total int `json:"total"` }
type Fault struct { Code int; Message string; Current *Case }
func (f *Fault) Error() string { return f.Message }
func Bad(message string) error { return &Fault{Code:400, Message:message} }
func NotFound() error { return &Fault{Code:404,Message:"case not found"} }
func Conflict(message string, current *Case) error { return &Fault{Code:409,Message:message,Current:current} }

func Load(path string) (*Store,error) {
 data,err:=os.ReadFile(path); if err!=nil { return nil,err }
 var seed Seed; if err=json.Unmarshal(data,&seed);err!=nil { return nil,err }
 return New(seed)
}
func New(seed Seed) (*Store,error) {
 s:=&Store{orgs:append([]Organization{},seed.Organizations...),customers:append([]Customer{},seed.Customers...),cases:make(map[string]*Case)}
 orgIDs:=map[string]bool{}; for _,o:=range s.orgs {if o.ID==""||orgIDs[o.ID] {return nil,fmt.Errorf("invalid organization id")};orgIDs[o.ID]=true}
 custIDs:=map[string]string{}; for _,c:=range s.customers {if c.ID==""||!orgIDs[c.OrgID]||custIDs[c.ID]!="" {return nil,fmt.Errorf("invalid customer %q",c.ID)};custIDs[c.ID]=c.OrgID}
 for _,c:=range seed.Cases {
  if c.ID==""||s.cases[c.ID]!=nil||c.OrgID!=custIDs[c.CustomerID]||c.Revision<0 {return nil,fmt.Errorf("invalid case %q",c.ID)}
  if !oneOf(c.Status,"open","pending","resolved")||!oneOf(c.Priority,"low","medium","high") {return nil,fmt.Errorf("invalid case status/priority")}
  cp:=cloneCase(c);s.cases[c.ID]=&cp
 }
 return s,nil
}
func oneOf(v string, vals ...string) bool {for _,x:=range vals {if v==x{return true}};return false}
func cloneCase(c Case) Case {c.Tags=append([]string{},c.Tags...);c.Timeline=append([]Entry{},c.Timeline...);return c}
func (s *Store) Organizations() []Organization {s.mu.Lock();defer s.mu.Unlock();return append([]Organization{},s.orgs...)}
func (s *Store) Customers(org string) []Customer {
 s.mu.Lock();defer s.mu.Unlock();out:=[]Customer{};for _,c:=range s.customers{if c.OrgID==org{out=append(out,c)}};return out
}
func (s *Store) organizationExists(org string) bool {for _,o:=range s.orgs{if o.ID==org{return true}};return false}
func (s *Store) Detail(org,id string) (Case,error) {
 s.mu.Lock();defer s.mu.Unlock()
 c:=s.cases[id];if c==nil||c.OrgID!=org{return Case{},NotFound()};return cloneCase(*c),nil
}
func (s *Store) List(org,q,status string,offset,limit int) (ListResult,error) {
 if org=="" {return ListResult{},Bad("org is required")}
 if offset<0||offset>100000||limit<1||limit>100 {return ListResult{},Bad("invalid pagination")}
 if !oneOf(status,"all","open","pending","resolved") {return ListResult{},Bad("invalid status")}
 s.mu.Lock();defer s.mu.Unlock()
 if !s.organizationExists(org){return ListResult{},Bad("unknown organization")}
 needle:=strings.ToLower(strings.TrimSpace(q));all:=[]Case{}
 for _,c:=range s.cases {
  if c.OrgID!=org||(status!="all"&&c.Status!=status){continue}
  if needle!=""&&!strings.Contains(strings.ToLower(c.Subject+" "+c.ID+" "+c.CustomerID),needle){continue}
  all=append(all,cloneCase(*c))
 }
 sort.Slice(all,func(i,j int)bool{return all[i].ID<all[j].ID})
 total:=len(all);if offset>=total{return ListResult{Cases:[]Case{},Total:total},nil}
 end:=offset+limit;if end>total{end=total};return ListResult{Cases:all[offset:end],Total:total},nil
}
func (s *Store) UpdateNote(org,id string,expectedRevision int,note string) (Case,error) {
 if expectedRevision<0{return Case{},Bad("invalid expectedRevision")}
 note=strings.TrimSpace(note);if len(note)>500{return Case{},Bad("note exceeds 500 characters")}
 s.mu.Lock();defer s.mu.Unlock()
 c:=s.cases[id];if c==nil||c.OrgID!=org{return Case{},NotFound()}
 if c.Revision!=expectedRevision {copy:=cloneCase(*c);return Case{},Conflict("case changed; refresh before saving",&copy)}
 if note!=c.Note{c.Note=note;c.Revision++}
 return cloneCase(*c),nil
}
