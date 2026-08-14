package store

import (
	"encoding/json"
	"errors"
	"os"
	"sync"

	"queuepilot/internal/domain"
)

type Store struct { mu sync.Mutex; opportunities map[string]domain.Opportunity; reps map[string]domain.Rep }

func New(rosterPath string) (*Store, error) { data, err := os.ReadFile(rosterPath); if err != nil { return nil, err }; var reps []domain.Rep; if err := json.Unmarshal(data, &reps); err != nil { return nil, err }; s := &Store{opportunities: seedOpportunities(), reps: map[string]domain.Rep{}}; for _, rep := range reps { s.reps[rep.ID] = rep }; return s, nil }
func seedOpportunities() map[string]domain.Opportunity { rows := []domain.Opportunity{{ID:"opp-101",Account:"Acme Robotics",Region:"west",Stage:"qualified",OwnerID:"rep-ava",PriorityScore:98,Revision:1},{ID:"opp-102",Account:"Beacon Health",Region:"east",Stage:"proposal",OwnerID:"rep-ben",PriorityScore:95,Revision:3},{ID:"opp-103",Account:"Cedar Labs",Region:"west",Stage:"discovery",OwnerID:"rep-ava",PriorityScore:91,Revision:1},{ID:"opp-104",Account:"Delta Freight",Region:"central",Stage:"qualified",OwnerID:"rep-cam",PriorityScore:91,Revision:2},{ID:"opp-105",Account:"Echo Security",Region:"east",Stage:"proposal",OwnerID:"rep-ben",PriorityScore:88,Revision:1},{ID:"opp-106",Account:"Flux Energy",Region:"west",Stage:"qualified",OwnerID:"rep-ava",PriorityScore:84,Revision:4},{ID:"opp-107",Account:"Grove Retail",Region:"central",Stage:"closed_won",OwnerID:"rep-cam",PriorityScore:82,Revision:2},{ID:"opp-108",Account:"Harbor AI",Region:"east",Stage:"qualified",OwnerID:"rep-ben",PriorityScore:79,Revision:1},{ID:"opp-109",Account:"Ion Works",Region:"west",Stage:"proposal",OwnerID:"rep-ava",PriorityScore:77,Revision:2},{ID:"opp-110",Account:"Juniper Foods",Region:"central",Stage:"discovery",OwnerID:"rep-cam",PriorityScore:72,Revision:1}}; m:=map[string]domain.Opportunity{}; for _, row := range rows { m[row.ID]=row }; return m }
func (s *Store) Snapshot() ([]domain.Opportunity, []domain.Rep) { s.mu.Lock(); defer s.mu.Unlock(); opps:=make([]domain.Opportunity,0,len(s.opportunities)); for _,o:=range s.opportunities{opps=append(opps,o)}; reps:=make([]domain.Rep,0,len(s.reps)); for _,r:=range s.reps{reps=append(reps,r)}; return opps,reps }
func (s *Store) GetOpportunity(id string)(domain.Opportunity,bool){s.mu.Lock();defer s.mu.Unlock();o,ok:=s.opportunities[id];return o,ok}
func (s *Store) GetRep(id string)(domain.Rep,bool){s.mu.Lock();defer s.mu.Unlock();r,ok:=s.reps[id];return r,ok}
func (s *Store) ActiveCount(ownerID string) int { s.mu.Lock(); defer s.mu.Unlock(); return s.activeCountLocked(ownerID) }
func (s *Store) activeCountLocked(ownerID string) int { n:=0; for _,o:=range s.opportunities{if o.OwnerID==ownerID && o.Stage!="closed_won" && o.Stage!="closed_lost"{n++}}; return n }
func (s *Store) Reassign(id,target string,expectedRevision int)(domain.Opportunity,error){s.mu.Lock();defer s.mu.Unlock();o,ok:=s.opportunities[id];if !ok{return domain.Opportunity{},errors.New("not_found")};if o.Revision!=expectedRevision{return domain.Opportunity{},errors.New("stale")};if o.Stage=="closed_won"||o.Stage=="closed_lost"{return domain.Opportunity{},errors.New("closed")};rep,ok:=s.reps[target];if !ok{return domain.Opportunity{},errors.New("rep_not_found")};allowed:=false;for _,region:=range rep.Regions{if region==o.Region{allowed=true}};if !allowed{return domain.Opportunity{},errors.New("region_mismatch")};if o.OwnerID!=target&&s.activeCountLocked(target)>=rep.MaxActive{return domain.Opportunity{},errors.New("capacity")};o.OwnerID=target;o.Revision++;s.opportunities[id]=o;return o,nil}
