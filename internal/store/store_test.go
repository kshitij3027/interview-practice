package store

import (
	"testing"
	"time"

	"interview-practice/returnscan/internal/model"
)

func seedCase() model.ReturnCase {
	return model.ReturnCase{ID: "R1", OrderID: "O1", Warehouse: "SFO", CreatedAt: time.Date(2026, 9, 1, 10, 0, 0, 0, time.UTC), ExpectedParcels: []string{"P1", "P2"}, ReceivedParcels: []string{"P1"}, Status: "partial", Revision: 2}
}

func TestSetExceptionChangedAndNoOp(t *testing.T) {
	s := New([]model.ReturnCase{seedCase()})
	c, dr, changed, err := s.SetException("R1", 2, true, "box torn")
	if err != nil || !changed || c.Revision != 3 || dr != 2 || !c.Exception.Active {
		t.Fatalf("unexpected first mutation: %+v %d %v %v", c, dr, changed, err)
	}
	c, dr, changed, err = s.SetException("R1", 3, true, "box torn")
	if err != nil || changed || c.Revision != 3 || dr != 2 {
		t.Fatalf("no-op changed state: %+v %d %v %v", c, dr, changed, err)
	}
}

func TestSetExceptionRequiresRevision(t *testing.T) {
	s := New([]model.ReturnCase{seedCase()})
	_, dr, changed, err := s.SetException("R1", 1, true, "x")
	if err != ErrStale || changed || dr != 1 {
		t.Fatalf("expected stale without mutation: %v %v %d", err, changed, dr)
	}
}

func TestSetExceptionValidatesReasonAndClear(t *testing.T) {
	s := New([]model.ReturnCase{seedCase()})
	if _, _, _, err := s.SetException("R1", 2, true, "   "); err != ErrInvalidReason {
		t.Fatalf("expected invalid reason, got %v", err)
	}
	c, _, _, err := s.SetException("R1", 2, true, "damage")
	if err != nil {
		t.Fatal(err)
	}
	c, _, changed, err := s.SetException("R1", c.Revision, false, "ignored")
	if err != nil || !changed || c.Exception.Active || c.Exception.Reason != "" {
		t.Fatalf("clear failed: %+v %v", c, err)
	}
}

func TestSnapshotFiltersAndOrders(t *testing.T) {
	a := seedCase()
	b := seedCase()
	b.ID = "R0"
	b.Warehouse = "LAX"
	b.Status = "awaiting"
	b.ReceivedParcels = nil
	s := New([]model.ReturnCase{a, b})
	snap := s.Snapshot("LAX", "awaiting")
	if len(snap.Cases) != 1 || snap.Cases[0].ID != "R0" {
		t.Fatalf("unexpected snapshot: %+v", snap)
	}
}
