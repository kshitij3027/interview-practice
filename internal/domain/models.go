package domain

type Opportunity struct {
	ID            string `json:"id"`
	Account       string `json:"account"`
	Region        string `json:"region"`
	Stage         string `json:"stage"`
	OwnerID       string `json:"owner_id"`
	PriorityScore int    `json:"priority_score"`
	Revision      int    `json:"revision"`
}

type Rep struct {
	ID        string   `json:"id"`
	Name      string   `json:"name"`
	Regions   []string `json:"regions"`
	MaxActive int      `json:"max_active"`
}

type OpportunityPage struct {
	Items      []Opportunity `json:"items"`
	NextCursor string        `json:"next_cursor,omitempty"`
}
