package main

import (
	"log"
	"net/http"
	"os"

	"queuepilot/internal/httpapi"
	"queuepilot/internal/service"
	"queuepilot/internal/store"
)

func main() {
	roster := "fixtures/rep_roster.json"
	if v := os.Getenv("ROSTER_PATH"); v != "" {
		roster = v
	}
	s, err := store.New(roster)
	if err != nil {
		log.Fatal(err)
	}
	api := httpapi.API{Service: service.OpportunityService{Store: s}}
	log.Println("QueuePilot API listening on :3001")
	log.Fatal(http.ListenAndServe(":3001", api.Handler()))
}
