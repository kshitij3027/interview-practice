package fixtures

import (
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"
	"time"

	"interview-practice/returnscan/internal/model"
)

type rawCase struct {
	ID              string          `json:"id"`
	OrderID         string          `json:"order_id"`
	Warehouse       string          `json:"warehouse"`
	CreatedAt       string          `json:"created_at"`
	Closed          bool            `json:"closed"`
	ExpectedParcels []string        `json:"expected_parcels"`
	ReceivedParcels []string        `json:"received_parcels"`
	Revision        int             `json:"revision"`
	Exception       model.Exception `json:"exception"`
}

func LoadCases(path string) ([]model.ReturnCase, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var raw []rawCase
	if err := json.Unmarshal(b, &raw); err != nil {
		return nil, err
	}
	seen := map[string]bool{}
	out := make([]model.ReturnCase, 0, len(raw))
	for _, r := range raw {
		if strings.TrimSpace(r.ID) == "" || seen[r.ID] {
			return nil, fmt.Errorf("invalid or duplicate return id %q", r.ID)
		}
		seen[r.ID] = true
		t, err := time.Parse(time.RFC3339, r.CreatedAt)
		if err != nil {
			return nil, fmt.Errorf("%s created_at: %w", r.ID, err)
		}
		if len(r.ExpectedParcels) == 0 {
			return nil, fmt.Errorf("%s has no expected parcels", r.ID)
		}
		expected := map[string]bool{}
		for _, p := range r.ExpectedParcels {
			if p == "" || expected[p] {
				return nil, fmt.Errorf("%s invalid expected parcel %q", r.ID, p)
			}
			expected[p] = true
		}
		for _, p := range r.ReceivedParcels {
			if !expected[p] {
				return nil, fmt.Errorf("%s received unknown parcel %q", r.ID, p)
			}
		}
		status := receiptStatus(len(r.ReceivedParcels), len(r.ExpectedParcels))
		out = append(out, model.ReturnCase{ID: r.ID, OrderID: r.OrderID, Warehouse: r.Warehouse, CreatedAt: t, Closed: r.Closed, ExpectedParcels: append([]string(nil), r.ExpectedParcels...), ReceivedParcels: append([]string(nil), r.ReceivedParcels...), Status: status, Revision: r.Revision, Exception: r.Exception})
	}
	return out, nil
}

func receiptStatus(received, expected int) string {
	if received == 0 {
		return "awaiting"
	}
	if received >= expected {
		return "received"
	}
	return "partial"
}

func LoadScans(path string) ([]model.ScanEvent, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	header, err := r.Read()
	if err != nil {
		return nil, err
	}
	want := []string{"batch_id", "scan_id", "parcel_id", "return_id_hint", "event_kind", "warehouse", "scanned_at", "ingested_at"}
	if len(header) != len(want) {
		return nil, fmt.Errorf("unexpected scan header")
	}
	for i := range want {
		if header[i] != want[i] {
			return nil, fmt.Errorf("unexpected scan column %d: %s", i, header[i])
		}
	}
	var out []model.ScanEvent
	for {
		rec, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		out = append(out, model.ScanEvent{BatchID: rec[0], ScanID: rec[1], ParcelID: rec[2], ReturnIDHint: rec[3], EventKind: rec[4], Warehouse: rec[5], ScannedAt: rec[6], IngestedAt: rec[7]})
	}
	return out, nil
}

func BatchIDs(scans []model.ScanEvent) []string {
	set := map[string]bool{}
	for _, s := range scans {
		if s.BatchID != "" {
			set[s.BatchID] = true
		}
	}
	out := make([]string, 0, len(set))
	for id := range set {
		out = append(out, id)
	}
	sort.Strings(out)
	return out
}
