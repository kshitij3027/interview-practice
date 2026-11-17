package workspace

import "testing"

func sample(t *testing.T)*Store{t.Helper();s,e:=New(Seed{Organizations:[]Organization{{ID:"org-x",Name:"X"},{ID:"org-y",Name:"Y"}},Customers:[]Customer{{ID:"cus-x",OrgID:"org-x",Name:"Customer"},{ID:"cus-y",OrgID:"org-y",Name:"Other"}},Cases:[]Case{{ID:"C-2",OrgID:"org-x",CustomerID:"cus-x",Subject:"Printer down",Status:"open",Priority:"high",Revision:2},{ID:"C-1",OrgID:"org-x",CustomerID:"cus-x",Subject:"Login issue",Status:"pending",Priority:"low",Revision:1},{ID:"C-3",OrgID:"org-y",CustomerID:"cus-y",Subject:"Other",Status:"open",Priority:"medium",Revision:1}}});if e!=nil{t.Fatal(e)};return s}
func TestListSortedAndScoped(t *testing.T){s:=sample(t);v,e:=s.List("org-x","","all",0,1);if e!=nil{t.Fatal(e)};if v.Total!=2||len(v.Cases)!=1||v.Cases[0].ID!="C-1"{t.Fatalf("bad listing: %+v",v)};v,e=s.List("org-x","LOGIN","all",0,20);if e!=nil||v.Total!=1||v.Cases[0].ID!="C-1"{t.Fatalf("search %+v %v",v,e)}}
func TestNotesConflictAndNoOp(t *testing.T){s:=sample(t);v,e:=s.UpdateNote("org-x","C-2",2," hi  ");if e!=nil||v.Note!="hi"||v.Revision!=3{t.Fatalf("change: %+v %v",v,e)};v,e=s.UpdateNote("org-x","C-2",3,"hi");if e!=nil||v.Revision!=3{t.Fatalf("no-op: %+v %v",v,e)};_,e=s.UpdateNote("org-x","C-2",2,"lost");if f,ok:=e.(*Fault);!ok||f.Code!=409{t.Fatalf("expected conflict: %v",e)}}
func TestHiddenCase(t *testing.T){s:=sample(t);_,e:=s.Detail("org-x","C-3");if f,ok:=e.(*Fault);!ok||f.Code!=404{t.Fatalf("cross-org leak: %v",e)}}
func TestCopiesDoNotMutate(t *testing.T){s:=sample(t);c,e:=s.Detail("org-x","C-1");if e!=nil{t.Fatal(e)};c.Tags=append(c.Tags,"unexpected");d,_:=s.Detail("org-x","C-1");if len(d.Tags)!=0{t.Fatal("returned slice is shared")}}
