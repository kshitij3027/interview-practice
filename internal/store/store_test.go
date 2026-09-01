package store

import "testing"

func loadTestStore(t *testing.T) *Store {
	t.Helper()
	s, err := Load("../../fixtures/customers.json")
	if err != nil {
		t.Fatal(err)
	}
	return s
}

func TestListFiltersAndSorts(t *testing.T) {
	s := loadTestStore(t)
	customers, revision := s.List("enterprise")
	if revision != 7 {
		t.Fatalf("revision=%d", revision)
	}
	if len(customers) != 3 {
		t.Fatalf("len=%d", len(customers))
	}
	if customers[0].ID != "cus_1001" || customers[1].ID != "cus_1002" || customers[2].ID != "cus_1003" {
		t.Fatalf("unexpected order: %#v", customers)
	}
}

func TestSetStatusUsesOptimisticRevision(t *testing.T) {
	s := loadTestStore(t)
	updated, datasetRevision, err := s.SetStatus("cus_1002", "active", 2)
	if err != nil {
		t.Fatal(err)
	}
	if updated.Status != "active" || updated.Revision != 3 || datasetRevision != 8 {
		t.Fatalf("unexpected update: %#v revision=%d", updated, datasetRevision)
	}
	_, _, err = s.SetStatus("cus_1002", "paused", 2)
	if err != ErrStaleRevision {
		t.Fatalf("expected stale revision, got %v", err)
	}
}

func TestInvalidStatusDoesNotMutate(t *testing.T) {
	s := loadTestStore(t)
	_, _, err := s.SetStatus("cus_1001", "deleted", 4)
	if err != ErrInvalidStatus {
		t.Fatalf("expected invalid status, got %v", err)
	}
	customer, revision, err := s.Get("cus_1001")
	if err != nil {
		t.Fatal(err)
	}
	if customer.Revision != 4 || revision != 7 {
		t.Fatalf("state mutated: %#v rev=%d", customer, revision)
	}
}
