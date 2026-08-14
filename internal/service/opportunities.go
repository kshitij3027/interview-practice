package service

import (
	"encoding/base64"
	"fmt"
	"sort"
	"strconv"
	"strings"

	"queuepilot/internal/domain"
	"queuepilot/internal/store"
)

type OpportunityService struct{ Store *store.Store }

type ListFilter struct {
	Owner, Stage, Query, Cursor string
	Limit                       int
}

func (s OpportunityService) List(f ListFilter) domain.OpportunityPage {
	opps, _ := s.Store.Snapshot()
	filtered := make([]domain.Opportunity, 0)
	q := strings.ToLower(strings.TrimSpace(f.Query))
	for _, o := range opps {
		if f.Owner != "" && o.OwnerID != f.Owner { continue }
		if f.Stage != "" && o.Stage != f.Stage { continue }
		if q != "" && !strings.Contains(strings.ToLower(o.Account), q) { continue }
		filtered = append(filtered, o)
	}
	sort.Slice(filtered, func(i, j int) bool {
		if filtered[i].PriorityScore == filtered[j].PriorityScore { return filtered[i].ID < filtered[j].ID }
		return filtered[i].PriorityScore > filtered[j].PriorityScore
	})
	start := 0
	if f.Cursor != "" {
		if score, id, ok := decodeCursor(f.Cursor); ok {
			for i, o := range filtered {
				if o.PriorityScore < score || (o.PriorityScore == score && o.ID > id) { start = i; break }
				start = len(filtered)
			}
		}
	}
	limit := f.Limit
	if limit <= 0 || limit > 5 { limit = 3 }
	end := start + limit
	if end > len(filtered) { end = len(filtered) }
	items := filtered[start:end]
	page := domain.OpportunityPage{Items: items}
	if end < len(filtered) && len(items) > 0 {
		last := items[len(items)-1]
		page.NextCursor = encodeCursor(last.PriorityScore, last.ID)
	}
	return page
}

func (s OpportunityService) Reassign(id, target string, revision int) (domain.Opportunity, error) { return s.Store.Reassign(id, target, revision) }
func (s OpportunityService) Reps() []domain.Rep { _, reps := s.Store.Snapshot(); sort.Slice(reps, func(i, j int) bool { return reps[i].ID < reps[j].ID }); return reps }
func encodeCursor(score int, id string) string { return base64.RawURLEncoding.EncodeToString([]byte(fmt.Sprintf("%d|%s", score, id))) }
func decodeCursor(c string) (int, string, bool) { b, err := base64.RawURLEncoding.DecodeString(c); if err != nil { return 0, "", false }; parts := strings.SplitN(string(b), "|", 2); if len(parts) != 2 { return 0, "", false }; n, err := strconv.Atoi(parts[0]); if err != nil { return 0, "", false }; return n, parts[1], true }
