package service

import (
	"queuepilot/internal/store"
	"testing"
)

func svc(t *testing.T) OpportunityService { t.Helper(); s, err := store.New("../../fixtures/rep_roster.json"); if err != nil { t.Fatal(err) }; return OpportunityService{Store: s} }
func TestListUsesStablePriorityOrder(t *testing.T) { s := svc(t); p := s.List(ListFilter{Limit: 4}); got := []string{}; for _, o := range p.Items { got = append(got, o.ID) }; want := []string{"opp-101", "opp-102", "opp-103", "opp-104"}; for i := range want { if got[i] != want[i] { t.Fatalf("got %v want %v", got, want) } }; if p.NextCursor == "" { t.Fatal("expected cursor") } }
func TestCursorContinuesAfterTie(t *testing.T) { s := svc(t); p1 := s.List(ListFilter{Limit: 3}); p2 := s.List(ListFilter{Limit: 3, Cursor: p1.NextCursor}); if p2.Items[0].ID != "opp-104" { t.Fatalf("unexpected next item: %s", p2.Items[0].ID) } }
func TestFiltersCompose(t *testing.T) { s := svc(t); p := s.List(ListFilter{Owner: "rep-ava", Stage: "qualified", Query: "flux", Limit: 5}); if len(p.Items) != 1 || p.Items[0].ID != "opp-106" { t.Fatalf("unexpected %+v", p.Items) } }
