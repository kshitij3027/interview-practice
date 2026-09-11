package catalog_test

import (
	"strings"
	"testing"

	"promoscope/internal/catalog"
	"promoscope/internal/parse"
)

func TestBuildComputesAncestry(t *testing.T) {
	cats, err := parse.Categories(strings.NewReader("category_id,parent_id,name\nroot,,Root\na,root,A\nb,a,B\n"))
	if err != nil {
		t.Fatal(err)
	}
	products, err := parse.Products(strings.NewReader("product_id,category_id,seller_id\np,b,s\n"))
	if err != nil {
		t.Fatal(err)
	}
	promos, err := parse.Promotions(strings.NewReader("promotion_id,target_type,target_id,region,starts_at,ends_at,priority,discount_bps\nx,category,a,*,2026-01-01T00:00:00Z,2026-02-01T00:00:00Z,1,100\n"))
	if err != nil {
		t.Fatal(err)
	}
	c, err := catalog.Build(cats, products, promos)
	if err != nil {
		t.Fatal(err)
	}
	if c.Depth["b"] != 2 {
		t.Fatalf("depth b = %d", c.Depth["b"])
	}
	got := strings.Join(c.Ancestors["b"], ",")
	if got != "b,a,root" {
		t.Fatalf("ancestors b = %s", got)
	}
}

func TestBuildRejectsHierarchyCycle(t *testing.T) {
	cats, _ := parse.Categories(strings.NewReader("category_id,parent_id,name\na,b,A\nb,a,B\n"))
	_, err := catalog.Build(cats, nil, nil)
	if err == nil {
		t.Fatal("expected cycle error")
	}
}

func TestExactPromotionReplayIsDeduplicated(t *testing.T) {
	cats, _ := parse.Categories(strings.NewReader("category_id,parent_id,name\nroot,,Root\n"))
	products, _ := parse.Products(strings.NewReader("product_id,category_id,seller_id\np,root,s\n"))
	promos, err := parse.Promotions(strings.NewReader("promotion_id,target_type,target_id,region,starts_at,ends_at,priority,discount_bps\nx,product,p,*,2026-01-01T00:00:00Z,2026-02-01T00:00:00Z,1,100\nx,product,p,*,2026-01-01T00:00:00Z,2026-02-01T00:00:00Z,1,100\n"))
	if err != nil {
		t.Fatal(err)
	}
	c, err := catalog.Build(cats, products, promos)
	if err != nil {
		t.Fatal(err)
	}
	if len(c.Promotions) != 1 {
		t.Fatalf("promotions = %d", len(c.Promotions))
	}
}
