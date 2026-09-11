package parse

import (
	"bufio"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"io"
	"strconv"
	"strings"
	"time"

	"promoscope/internal/model"
)

const timestampLayout = time.RFC3339

func Categories(r io.Reader) ([]model.Category, error) {
	rows, err := csv.NewReader(r).ReadAll()
	if err != nil {
		return nil, err
	}
	if len(rows) == 0 || strings.Join(rows[0], ",") != "category_id,parent_id,name" {
		return nil, fmt.Errorf("categories: expected header category_id,parent_id,name")
	}
	out := make([]model.Category, 0, len(rows)-1)
	for i, row := range rows[1:] {
		if len(row) != 3 {
			return nil, fmt.Errorf("categories row %d: expected 3 columns", i+2)
		}
		out = append(out, model.Category{ID: strings.TrimSpace(row[0]), ParentID: strings.TrimSpace(row[1]), Name: strings.TrimSpace(row[2])})
	}
	return out, nil
}

func Products(r io.Reader) ([]model.Product, error) {
	rows, err := csv.NewReader(r).ReadAll()
	if err != nil {
		return nil, err
	}
	if len(rows) == 0 || strings.Join(rows[0], ",") != "product_id,category_id,seller_id" {
		return nil, fmt.Errorf("products: expected header product_id,category_id,seller_id")
	}
	out := make([]model.Product, 0, len(rows)-1)
	for i, row := range rows[1:] {
		if len(row) != 3 {
			return nil, fmt.Errorf("products row %d: expected 3 columns", i+2)
		}
		out = append(out, model.Product{ID: strings.TrimSpace(row[0]), CategoryID: strings.TrimSpace(row[1]), SellerID: strings.TrimSpace(row[2])})
	}
	return out, nil
}

func Promotions(r io.Reader) ([]model.Promotion, error) {
	rows, err := csv.NewReader(r).ReadAll()
	if err != nil {
		return nil, err
	}
	if len(rows) == 0 || strings.Join(rows[0], ",") != "promotion_id,target_type,target_id,region,starts_at,ends_at,priority,discount_bps" {
		return nil, fmt.Errorf("promotions: unexpected header")
	}
	out := make([]model.Promotion, 0, len(rows)-1)
	for i, row := range rows[1:] {
		if len(row) != 8 {
			return nil, fmt.Errorf("promotions row %d: expected 8 columns", i+2)
		}
		start, err := time.Parse(timestampLayout, strings.TrimSpace(row[4]))
		if err != nil {
			return nil, fmt.Errorf("promotions row %d starts_at: %w", i+2, err)
		}
		end, err := time.Parse(timestampLayout, strings.TrimSpace(row[5]))
		if err != nil {
			return nil, fmt.Errorf("promotions row %d ends_at: %w", i+2, err)
		}
		priority, err := strconv.Atoi(strings.TrimSpace(row[6]))
		if err != nil {
			return nil, fmt.Errorf("promotions row %d priority: %w", i+2, err)
		}
		discount, err := strconv.Atoi(strings.TrimSpace(row[7]))
		if err != nil {
			return nil, fmt.Errorf("promotions row %d discount_bps: %w", i+2, err)
		}
		out = append(out, model.Promotion{
			ID: strings.TrimSpace(row[0]), TargetType: strings.TrimSpace(row[1]), TargetID: strings.TrimSpace(row[2]), Region: strings.TrimSpace(row[3]),
			StartsAt: start.UTC(), EndsAt: end.UTC(), Priority: priority, DiscountBPS: discount,
		})
	}
	return out, nil
}

func Queries(r io.Reader) ([]model.Query, error) {
	scanner := bufio.NewScanner(r)
	var out []model.Query
	line := 0
	for scanner.Scan() {
		line++
		text := strings.TrimSpace(scanner.Text())
		if text == "" {
			continue
		}
		var raw struct {
			RequestID string `json:"request_id"`
			ProductID string `json:"product_id"`
			Region    string `json:"region"`
			AsOf      string `json:"as_of"`
		}
		if err := json.Unmarshal([]byte(text), &raw); err != nil {
			return nil, fmt.Errorf("queries line %d: %w", line, err)
		}
		asOf, err := time.Parse(timestampLayout, raw.AsOf)
		if err != nil {
			return nil, fmt.Errorf("queries line %d as_of: %w", line, err)
		}
		out = append(out, model.Query{RequestID: raw.RequestID, ProductID: raw.ProductID, Region: raw.Region, AsOf: asOf.UTC()})
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return out, nil
}
