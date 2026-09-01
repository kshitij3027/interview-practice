package service

import (
	"testing"

	"interview-practice/customermerge/internal/store"
)

func testService(t *testing.T) *CustomerService {
	t.Helper()
	s, err := store.Load("../../fixtures/customers.json")
	if err != nil {
		t.Fatal(err)
	}
	return NewCustomerService(s)
}

func TestDetailReturnsDatasetRevision(t *testing.T) {
	svc := testService(t)
	detail, err := svc.Detail("cus_1005")
	if err != nil {
		t.Fatal(err)
	}
	if detail.Customer.Name != "BrightCart" || detail.DatasetRevision != 7 {
		t.Fatalf("unexpected detail: %#v", detail)
	}
}

func TestSetStatusTrimsInput(t *testing.T) {
	svc := testService(t)
	detail, err := svc.SetStatus("cus_1004", " active ", 1)
	if err != nil {
		t.Fatal(err)
	}
	if detail.Customer.Status != "active" || detail.Customer.Revision != 2 || detail.DatasetRevision != 8 {
		t.Fatalf("unexpected result: %#v", detail)
	}
}
