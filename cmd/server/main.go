package main

import (
	"log"
	"net/http"

	"interview-practice/customermerge/internal/httpapi"
	"interview-practice/customermerge/internal/service"
	"interview-practice/customermerge/internal/store"
)

func main() {
	s, err := store.Load("fixtures/customers.json")
	if err != nil {
		log.Fatal(err)
	}
	api := httpapi.New(service.NewCustomerService(s))
	log.Println("MergeDesk running at http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", api.Handler()))
}
