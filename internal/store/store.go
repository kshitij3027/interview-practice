package store

import (
	"errors"
	"sort"
	"strings"
	"sync"

	"interview-practice/returnscan/internal/model"
)

var (
	ErrNotFound     = errors.New("return not found")
	ErrStale        = errors.New("stale return revision")
	ErrInvalidReason = errors.New("exception reason is required")
)

type Store struct {
	mu              sync.Mutex
	cases           map[string]model.ReturnCase
	datasetRevision int
}

func New(cases []model.ReturnCase) *Store {
	s := &Store{cases: map[string]model.ReturnCase{}, datasetRevision: 1}
	for _, c := range cases {
		s.cases[c.ID] = cloneCase(c)
	}
	return s
}

func cloneCase(c model.ReturnCase) model.ReturnCase {
	c.ExpectedParcels = append([]string(nil), c.ExpectedParcels...)
	c.ReceivedParcels = append([]string(nil), c.ReceivedParcels...)
	return c
}

func (s *Store) Snapshot(warehouse, status string) model.Snapshot {
	s.mu.Lock()
	defer s.mu.Unlock()
	rows := make([]model.ReturnCase, 0, len(s.cases))
	for _, c := range s.cases {
		if warehouse != "" && c.Warehouse != warehouse {
			continue
		}
		if status != "" && c.Status != status {
			continue
		}
		rows = append(rows, cloneCase(c))
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].Warehouse != rows[j].Warehouse {
			return rows[i].Warehouse < rows[j].Warehouse
		}
		if !rows[i].CreatedAt.Equal(rows[j].CreatedAt) {
			return rows[i].CreatedAt.Before(rows[j].CreatedAt)
		}
		return rows[i].ID < rows[j].ID
	})
	return model.Snapshot{DatasetRevision: s.datasetRevision, Cases: rows}
}

func (s *Store) Get(id string) (model.ReturnCase, int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	c, ok := s.cases[id]
	if !ok {
		return model.ReturnCase{}, s.datasetRevision, ErrNotFound
	}
	return cloneCase(c), s.datasetRevision, nil
}

func (s *Store) SetException(id string, expectedRevision int, active bool, reason string) (model.ReturnCase, int, bool, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	c, ok := s.cases[id]
	if !ok {
		return model.ReturnCase{}, s.datasetRevision, false, ErrNotFound
	}
	if c.Revision != expectedRevision {
		return cloneCase(c), s.datasetRevision, false, ErrStale
	}
	reason = strings.TrimSpace(reason)
	if active && reason == "" {
		return cloneCase(c), s.datasetRevision, false, ErrInvalidReason
	}
	if !active {
		reason = ""
	}
	if c.Exception.Active == active && c.Exception.Reason == reason {
		return cloneCase(c), s.datasetRevision, false, nil
	}
	c.Exception = model.Exception{Active: active, Reason: reason}
	c.Revision++
	s.datasetRevision++
	s.cases[id] = c
	return cloneCase(c), s.datasetRevision, true, nil
}
