package catalog

import (
	"fmt"
	"sort"

	"promoscope/internal/model"
)

type Catalog struct {
	Categories map[string]model.Category
	Products   map[string]model.Product
	Promotions map[string]model.Promotion
	Depth      map[string]int
	Ancestors  map[string][]string
}

func Build(categories []model.Category, products []model.Product, promotions []model.Promotion) (*Catalog, error) {
	c := &Catalog{
		Categories: make(map[string]model.Category),
		Products:   make(map[string]model.Product),
		Promotions: make(map[string]model.Promotion),
		Depth:      make(map[string]int),
		Ancestors:  make(map[string][]string),
	}

	for _, cat := range categories {
		if cat.ID == "" {
			return nil, fmt.Errorf("category id cannot be empty")
		}
		if _, exists := c.Categories[cat.ID]; exists {
			return nil, fmt.Errorf("duplicate category_id %q", cat.ID)
		}
		c.Categories[cat.ID] = cat
	}
	for id, cat := range c.Categories {
		if cat.ParentID != "" {
			if _, ok := c.Categories[cat.ParentID]; !ok {
				return nil, fmt.Errorf("category %q references unknown parent %q", id, cat.ParentID)
			}
		}
	}

	state := make(map[string]uint8)
	var visit func(string) (int, []string, error)
	visit = func(id string) (int, []string, error) {
		if state[id] == 1 {
			return 0, nil, fmt.Errorf("category hierarchy contains a cycle at %q", id)
		}
		if state[id] == 2 {
			return c.Depth[id], c.Ancestors[id], nil
		}
		state[id] = 1
		cat := c.Categories[id]
		depth := 0
		anc := []string{id}
		if cat.ParentID != "" {
			pd, pa, err := visit(cat.ParentID)
			if err != nil {
				return 0, nil, err
			}
			depth = pd + 1
			anc = append(anc, pa...)
		}
		state[id] = 2
		c.Depth[id] = depth
		c.Ancestors[id] = anc
		return depth, anc, nil
	}
	ids := make([]string, 0, len(c.Categories))
	for id := range c.Categories {
		ids = append(ids, id)
	}
	sort.Strings(ids)
	for _, id := range ids {
		if _, _, err := visit(id); err != nil {
			return nil, err
		}
	}

	for _, p := range products {
		if p.ID == "" {
			return nil, fmt.Errorf("product id cannot be empty")
		}
		if _, exists := c.Products[p.ID]; exists {
			return nil, fmt.Errorf("duplicate product_id %q", p.ID)
		}
		if _, ok := c.Categories[p.CategoryID]; !ok {
			return nil, fmt.Errorf("product %q references unknown category %q", p.ID, p.CategoryID)
		}
		c.Products[p.ID] = p
	}

	for _, p := range promotions {
		if p.ID == "" {
			return nil, fmt.Errorf("promotion id cannot be empty")
		}
		if p.TargetType != "category" && p.TargetType != "product" {
			return nil, fmt.Errorf("promotion %q has invalid target_type %q", p.ID, p.TargetType)
		}
		if p.Region == "" {
			return nil, fmt.Errorf("promotion %q has empty region", p.ID)
		}
		if !p.StartsAt.Before(p.EndsAt) {
			return nil, fmt.Errorf("promotion %q has non-positive time window", p.ID)
		}
		if p.DiscountBPS < 0 || p.DiscountBPS > 10000 {
			return nil, fmt.Errorf("promotion %q has invalid discount_bps", p.ID)
		}
		if p.TargetType == "category" {
			if _, ok := c.Categories[p.TargetID]; !ok {
				return nil, fmt.Errorf("promotion %q references unknown category %q", p.ID, p.TargetID)
			}
		} else if _, ok := c.Products[p.TargetID]; !ok {
			return nil, fmt.Errorf("promotion %q references unknown product %q", p.ID, p.TargetID)
		}

		if existing, ok := c.Promotions[p.ID]; ok {
			if existing != p {
				return nil, fmt.Errorf("promotion_id %q has conflicting definitions", p.ID)
			}
			continue
		}
		c.Promotions[p.ID] = p
	}

	return c, nil
}
