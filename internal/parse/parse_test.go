package parse_test

import (
	"strings"
	"testing"

	"promoscope/internal/parse"
)

func TestQueriesSkipBlankLinesAndNormalizeUTC(t *testing.T) {
	qs, err := parse.Queries(strings.NewReader("{\"request_id\":\"q\",\"product_id\":\"p\",\"region\":\"us\",\"as_of\":\"2026-09-11T01:00:00-07:00\"}\n\n"))
	if err != nil {
		t.Fatal(err)
	}
	if len(qs) != 1 {
		t.Fatalf("queries = %d", len(qs))
	}
	if got := qs[0].AsOf.Format("2006-01-02T15:04:05Z07:00"); got != "2026-09-11T08:00:00Z" {
		t.Fatalf("as_of = %s", got)
	}
}
