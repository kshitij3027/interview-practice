package model

import "time"

type Pool struct {
	ID              string
	Region          string
	SKU             string
	Tags            map[string]struct{}
	UnitPriceMicros int64
	BaseCapacity    int
}

type CapacityEvent struct {
	ID          string
	PoolID      string
	EffectiveAt time.Time
	DeltaUnits  int
}

type Reservation struct {
	ID      string
	PoolID  string
	StartAt time.Time
	EndAt   time.Time
	Units   int
}

type Query struct {
	RequestID       string   `json:"request_id"`
	Region          string   `json:"region"`
	SKU             string   `json:"sku"`
	RequiredTags    []string `json:"required_tags"`
	Units           int      `json:"units"`
	DurationMinutes int      `json:"duration_minutes"`
	EarliestStart   string   `json:"earliest_start"`
	LatestFinish    string   `json:"latest_finish"`
}

type Snapshot struct {
	Pools        []Pool
	Events       []CapacityEvent
	Reservations []Reservation
	Queries      []Query
}
