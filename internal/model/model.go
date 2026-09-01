package model

type FieldValue struct {
	Value     string `json:"value"`
	Verified  bool   `json:"verified"`
	UpdatedAt string `json:"updated_at"`
}

type Activity struct {
	EventID    string `json:"event_id"`
	Type       string `json:"type"`
	OccurredAt string `json:"occurred_at"`
	Summary    string `json:"summary"`
}

type Customer struct {
	ID          string                `json:"id"`
	Name        string                `json:"name"`
	Segment     string                `json:"segment"`
	Status      string                `json:"status"`
	Revision    int                   `json:"revision"`
	Fields      map[string]FieldValue `json:"fields"`
	ExternalIDs map[string]string     `json:"external_ids"`
	Tags        []string              `json:"tags"`
	Activities  []Activity            `json:"activities"`
}

type Fixture struct {
	DatasetRevision int        `json:"dataset_revision"`
	Customers       []Customer `json:"customers"`
}
