package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"windowfinder/internal/load"
	"windowfinder/internal/planner"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "validate":
		run(false)
	case "resolve":
		run(true)
	default:
		usage()
		os.Exit(2)
	}
}

func run(resolve bool) {
	fs := flag.NewFlagSet(os.Args[1], flag.ExitOnError)
	pools := fs.String("pools", "", "pools CSV")
	events := fs.String("events", "", "capacity events CSV")
	reservations := fs.String("reservations", "", "reservations CSV")
	queries := fs.String("queries", "", "queries JSONL")
	_ = fs.Parse(os.Args[2:])
	if *pools == "" || *events == "" || *reservations == "" || *queries == "" {
		fmt.Fprintln(os.Stderr, "all four input paths are required")
		os.Exit(2)
	}
	snapshot, err := load.LoadSnapshot(*pools, *events, *reservations, *queries)
	if err != nil {
		fmt.Fprintln(os.Stderr, "validation error:", err)
		os.Exit(1)
	}
	if !resolve {
		fmt.Fprintf(os.Stdout, "validated %d pools / %d deduplicated events / %d deduplicated reservations / %d queries\n", len(snapshot.Pools), len(snapshot.Events), len(snapshot.Reservations), len(snapshot.Queries))
		return
	}
	results, err := planner.New(snapshot).ResolveAll()
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	for _, raw := range results {
		var v any
		if err := json.Unmarshal(raw, &v); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := enc.Encode(v); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: windowfinder <validate|resolve> --pools FILE --events FILE --reservations FILE --queries FILE")
}
