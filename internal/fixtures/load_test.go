package fixtures

import "testing"

func TestFixtureFilesLoad(t *testing.T) {
	cases, err := LoadCases("../../fixtures/returns.json")
	if err != nil {
		t.Fatal(err)
	}
	if len(cases) != 6 {
		t.Fatalf("expected 6 cases, got %d", len(cases))
	}
	scans, err := LoadScans("../../fixtures/carrier_scans.csv")
	if err != nil {
		t.Fatal(err)
	}
	if len(scans) < 10 {
		t.Fatalf("expected representative scan data")
	}
	ids := BatchIDs(scans)
	if len(ids) != 3 {
		t.Fatalf("expected 3 batches, got %v", ids)
	}
}
