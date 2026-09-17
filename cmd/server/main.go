package main

import (
	"log"
	"net/http"
	"os"

	"interview-practice/returnscan/internal/api"
	"interview-practice/returnscan/internal/fixtures"
	"interview-practice/returnscan/internal/store"
)

func main() {
	cases, err := fixtures.LoadCases("fixtures/returns.json")
	if err != nil {
		log.Fatal(err)
	}
	scans, err := fixtures.LoadScans("fixtures/carrier_scans.csv")
	if err != nil {
		log.Fatal(err)
	}
	s := api.New(store.New(cases), fixtures.BatchIDs(scans))
	mux := http.NewServeMux()
	mux.Handle("/api/", s.Handler())
	mux.Handle("/", http.FileServer(http.Dir("web")))
	addr := ":8080"
	if p := os.Getenv("PORT"); p != "" {
		addr = ":" + p
	}
	log.Printf("ReturnDock listening on http://localhost%s", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}
