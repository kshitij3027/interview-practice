package resolver

import (
	"errors"

	"promoscope/internal/catalog"
	"promoscope/internal/model"
)

var ErrUnavailable = errors.New("promotion resolution is not implemented in the starter")

type Resolver struct {
	catalog *catalog.Catalog
}

func New(c *catalog.Catalog) *Resolver {
	return &Resolver{catalog: c}
}

func (r *Resolver) Resolve(q model.Query) (model.Result, error) {
	_ = r.catalog
	_ = q
	return model.Result{}, ErrUnavailable
}
