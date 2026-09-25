package load

import (
	"os"
	"path/filepath"
	"testing"

	"windowfinder/internal/model"
)

func fixturePath(name string) string { return filepath.Join("..", "..", "fixtures", name) }

func TestFixtureSnapshotLoads(t *testing.T) {
	s, err := LoadSnapshot(fixturePath("pools.csv"), fixturePath("capacity_events.csv"), fixturePath("reservations.csv"), fixturePath("queries.jsonl"))
	if err != nil {
		t.Fatal(err)
	}
	if len(s.Pools) != 6 {
		t.Fatalf("pools=%d", len(s.Pools))
	}
	if len(s.Events) != 9 {
		t.Fatalf("events=%d", len(s.Events))
	}
	if len(s.Reservations) != 9 {
		t.Fatalf("reservations=%d", len(s.Reservations))
	}
	if len(s.Queries) != 9 {
		t.Fatalf("queries=%d", len(s.Queries))
	}
}

func TestExactDuplicateEventIsDeduplicated(t *testing.T) {
	d := t.TempDir()
	pools := filepath.Join(d, "p.csv")
	events := filepath.Join(d, "e.csv")
	reservations := filepath.Join(d, "r.csv")
	queries := filepath.Join(d, "q.jsonl")
	os.WriteFile(pools, []byte("pool_id,region,sku,tags,unit_price_micros,base_capacity\np1,r,s,,1,2\n"), 0644)
	row := "e1,p1,2026-09-25T09:00:00Z,-1\n"
	os.WriteFile(events, []byte("event_id,pool_id,effective_at,delta_units\n"+row+row), 0644)
	os.WriteFile(reservations, []byte("reservation_id,pool_id,start_at,end_at,units\n"), 0644)
	os.WriteFile(queries, []byte("{\"request_id\":\"q\",\"region\":\"r\",\"sku\":\"s\",\"required_tags\":[],\"units\":1,\"duration_minutes\":5,\"earliest_start\":\"2026-09-25T09:00:00Z\",\"latest_finish\":\"2026-09-25T09:10:00Z\"}\n"), 0644)
	s, err := LoadSnapshot(pools, events, reservations, queries)
	if err != nil {
		t.Fatal(err)
	}
	if len(s.Events) != 1 {
		t.Fatalf("events=%d", len(s.Events))
	}
}

func TestOversubscribedBaselineRejected(t *testing.T) {
	d := t.TempDir()
	pools := filepath.Join(d, "p.csv")
	events := filepath.Join(d, "e.csv")
	reservations := filepath.Join(d, "r.csv")
	queries := filepath.Join(d, "q.jsonl")
	os.WriteFile(pools, []byte("pool_id,region,sku,tags,unit_price_micros,base_capacity\np1,r,s,,1,1\n"), 0644)
	os.WriteFile(events, []byte("event_id,pool_id,effective_at,delta_units\n"), 0644)
	os.WriteFile(reservations, []byte("reservation_id,pool_id,start_at,end_at,units\nr1,p1,2026-09-25T09:00:00Z,2026-09-25T10:00:00Z,2\n"), 0644)
	os.WriteFile(queries, []byte("{\"request_id\":\"q\",\"region\":\"r\",\"sku\":\"s\",\"required_tags\":[],\"units\":1,\"duration_minutes\":5,\"earliest_start\":\"2026-09-25T09:00:00Z\",\"latest_finish\":\"2026-09-25T09:10:00Z\"}\n"), 0644)
	if _, err := LoadSnapshot(pools, events, reservations, queries); err == nil {
		t.Fatal("expected validation error")
	}
}

func TestOffsetEquivalentQueryTimes(t *testing.T) {
	q := modelQuery("2026-09-25T02:00:00-07:00", "2026-09-25T09:30:00Z")
	a, b, err := QueryTimes(q)
	if err != nil {
		t.Fatal(err)
	}
	if a.Format("15:04") != "09:00" || b.Format("15:04") != "09:30" {
		t.Fatalf("%s %s", a, b)
	}
}

func modelQuery(a, b string) model.Query { return model.Query{EarliestStart: a, LatestFinish: b} }
