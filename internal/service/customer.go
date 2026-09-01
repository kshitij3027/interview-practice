package service

import (
	"strings"

	"interview-practice/customermerge/internal/model"
	"interview-practice/customermerge/internal/store"
)

type CustomerService struct {
	store *store.Store
}

func NewCustomerService(s *store.Store) *CustomerService {
	return &CustomerService{store: s}
}

type CustomerList struct {
	Customers       []model.Customer `json:"customers"`
	DatasetRevision int              `json:"dataset_revision"`
}

type CustomerDetail struct {
	Customer        model.Customer `json:"customer"`
	DatasetRevision int            `json:"dataset_revision"`
}

func (s *CustomerService) List(segment string) CustomerList {
	customers, revision := s.store.List(segment)
	return CustomerList{Customers: customers, DatasetRevision: revision}
}

func (s *CustomerService) Detail(id string) (CustomerDetail, error) {
	customer, revision, err := s.store.Get(id)
	if err != nil {
		return CustomerDetail{}, err
	}
	return CustomerDetail{Customer: customer, DatasetRevision: revision}, nil
}

func (s *CustomerService) SetStatus(id, status string, expectedRevision int) (CustomerDetail, error) {
	customer, revision, err := s.store.SetStatus(id, strings.TrimSpace(status), expectedRevision)
	if err != nil {
		return CustomerDetail{}, err
	}
	return CustomerDetail{Customer: customer, DatasetRevision: revision}, nil
}
