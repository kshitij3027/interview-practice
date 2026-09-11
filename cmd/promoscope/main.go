package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"

	"promoscope/internal/catalog"
	"promoscope/internal/model"
	"promoscope/internal/parse"
	"promoscope/internal/resolver"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	cmd := os.Args[1]
	fs := flag.NewFlagSet(cmd, flag.ExitOnError)
	categoriesPath := fs.String("categories", "fixtures/categories.csv", "categories CSV")
	productsPath := fs.String("products", "fixtures/products.csv", "products CSV")
	promotionsPath := fs.String("promotions", "fixtures/promotions.csv", "promotions CSV")
	queriesPath := fs.String("queries", "fixtures/queries.jsonl", "queries JSONL")
	_ = fs.Parse(os.Args[2:])

	c, queries, err := load(*categoriesPath, *productsPath, *promotionsPath, *queriesPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}

	switch cmd {
	case "validate":
		fmt.Fprintf(os.Stdout, "validated %d categories / %d products / %d promotions / %d queries\n", len(c.Categories), len(c.Products), len(c.Promotions), len(queries))
	case "resolve":
		r := resolver.New(c)
		enc := json.NewEncoder(os.Stdout)
		for _, q := range queries {
			result, err := r.Resolve(q)
			if err != nil {
				if errors.Is(err, resolver.ErrUnavailable) {
					fmt.Fprintln(os.Stderr, err)
					os.Exit(3)
				}
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
			if err := enc.Encode(result); err != nil {
				fmt.Fprintln(os.Stderr, err)
				os.Exit(1)
			}
		}
	default:
		usage()
		os.Exit(2)
	}
}

func load(categoriesPath, productsPath, promotionsPath, queriesPath string) (*catalog.Catalog, []model.Query, error) {
	categoriesFile, err := os.Open(categoriesPath)
	if err != nil {
		return nil, nil, err
	}
	defer categoriesFile.Close()
	productsFile, err := os.Open(productsPath)
	if err != nil {
		return nil, nil, err
	}
	defer productsFile.Close()
	promotionsFile, err := os.Open(promotionsPath)
	if err != nil {
		return nil, nil, err
	}
	defer promotionsFile.Close()
	queriesFile, err := os.Open(queriesPath)
	if err != nil {
		return nil, nil, err
	}
	defer queriesFile.Close()

	categories, err := parse.Categories(categoriesFile)
	if err != nil {
		return nil, nil, err
	}
	products, err := parse.Products(productsFile)
	if err != nil {
		return nil, nil, err
	}
	promotions, err := parse.Promotions(promotionsFile)
	if err != nil {
		return nil, nil, err
	}
	queries, err := parse.Queries(queriesFile)
	if err != nil {
		return nil, nil, err
	}
	c, err := catalog.Build(categories, products, promotions)
	if err != nil {
		return nil, nil, err
	}
	return c, queries, nil
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: promoscope <validate|resolve> [--categories path --products path --promotions path --queries path]")
}
