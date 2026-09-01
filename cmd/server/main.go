package main

import (
	"log"
	"net/http"
	"os"

	"interview-practice/customermerge/internal/httpapi"
	"interview-practice/customermerge/internal/service"
	"interview-practice/customermerge/internal/store"
)

func main() {
	s, err := store.Load("fixtures/customers.json")
	if err != nil {
		log.Fatal(err)
	}
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	api := httpapi.New(service.NewCustomerService(s))
	log.Printf("MergeDesk running at http://localhost:%s", port)
	log.Fatal(http.ListenAndServe(":"+port, api.Handler()))
}
