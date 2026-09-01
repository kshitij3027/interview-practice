package store

import (
	"encoding/json"
	"errors"
	"os"
	"sort"
	"strings"
	"sync"

	"interview-practice/customermerge/internal/model"
)

var ErrNotFound = errors.New("customer not found")
var ErrStaleRevision = errors.New("stale revision")
var ErrInvalidStatus = errors.New("invalid status")

var allowedStatuses = map[string]bool{"prospect": true, "active": true, "paused": true}

type Store struct {
	mu              sync.RWMutex
	customers       map[string]model.Customer
	datasetRevision int
}

func Load(path string) (*Store, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var fixture model.Fixture
	if err := json.Unmarshal(data, &fixture); err != nil {
		return nil, err
	}
	customers := make(map[string]model.Customer, len(fixture.Customers))
	for _, customer := range fixture.Customers {
		customers[customer.ID] = customer
	}
	return &Store{customers: customers, datasetRevision: fixture.DatasetRevision}, nil
}

func (s *Store) List(segment string) ([]model.Customer, int) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	segment = strings.TrimSpace(strings.ToLower(segment))
	result := make([]model.Customer, 0, len(s.customers))
	for _, customer := range s.customers {
		if segment != "" && strings.ToLower(customer.Segment) != segment {
			continue
		}
		result = append(result, customer)
	}
	sort.Slice(result, func(i, j int) bool {
		if strings.ToLower(result[i].Name) == strings.ToLower(result[j].Name) {
			return result[i].ID < result[j].ID
		}
		return strings.ToLower(result[i].Name) < strings.ToLower(result[j].Name)
	})
	return result, s.datasetRevision
}

func (s *Store) Get(id string) (model.Customer, int, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	customer, ok := s.customers[id]
	if !ok {
		return model.Customer{}, s.datasetRevision, ErrNotFound
	}
	return customer, s.datasetRevision, nil
}

func (s *Store) SetStatus(id, status string, expectedRevision int) (model.Customer, int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	status = strings.TrimSpace(strings.ToLower(status))
	if !allowedStatuses[status] {
		return model.Customer{}, s.datasetRevision, ErrInvalidStatus
	}
	customer, ok := s.customers[id]
	if !ok {
		return model.Customer{}, s.datasetRevision, ErrNotFound
	}
	if customer.Revision != expectedRevision {
		return model.Customer{}, s.datasetRevision, ErrStaleRevision
	}
	customer.Status = status
	customer.Revision++
	s.datasetRevision++
	s.customers[id] = customer
	return customer, s.datasetRevision, nil
}
