package model

import "time"

type Exception struct {
	Active bool   `json:"active"`
	Reason string `json:"reason"`
}

type ReturnCase struct {
	ID              string    `json:"id"`
	OrderID         string    `json:"order_id"`
	Warehouse       string    `json:"warehouse"`
	CreatedAt       time.Time `json:"created_at"`
	Closed          bool      `json:"closed"`
	ExpectedParcels []string  `json:"expected_parcels"`
	ReceivedParcels []string  `json:"received_parcels"`
	Status          string    `json:"status"`
	Revision        int       `json:"revision"`
	Exception       Exception `json:"exception"`
}

type ScanEvent struct {
	BatchID      string
	ScanID       string
	ParcelID     string
	ReturnIDHint string
	EventKind    string
	Warehouse    string
	ScannedAt    string
	IngestedAt   string
}

type Snapshot struct {
	DatasetRevision int          `json:"dataset_revision"`
	Cases           []ReturnCase `json:"cases"`
}
