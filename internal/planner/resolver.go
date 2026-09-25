package planner

import (
	"encoding/json"
	"errors"

	"windowfinder/internal/model"
)

var ErrNotImplemented = errors.New("resolver not implemented")

type Resolver struct {
	snapshot model.Snapshot
}

func New(snapshot model.Snapshot) *Resolver {
	return &Resolver{snapshot: snapshot}
}

func (r *Resolver) ResolveAll() ([]json.RawMessage, error) {
	return nil, ErrNotImplemented
}
