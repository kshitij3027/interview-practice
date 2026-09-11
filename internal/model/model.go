package model

import "time"

type Category struct {
	ID       string
	ParentID string
	Name     string
}

type Product struct {
	ID         string
	CategoryID string
	SellerID   string
}

type Promotion struct {
	ID          string
	TargetType  string
	TargetID    string
	Region      string
	StartsAt    time.Time
	EndsAt      time.Time
	Priority    int
	DiscountBPS int
}

type Query struct {
	RequestID string    `json:"request_id"`
	ProductID string    `json:"product_id"`
	Region    string    `json:"region"`
	AsOf      time.Time `json:"as_of"`
}

type Result struct {
	RequestID   string `json:"request_id"`
	Status      string `json:"status"`
	PromotionID string `json:"promotion_id,omitempty"`
	DiscountBPS int    `json:"discount_bps,omitempty"`
	Scope       string `json:"scope,omitempty"`
	Reason      string `json:"reason,omitempty"`
}
