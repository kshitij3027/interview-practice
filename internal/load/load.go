package load

import (
	"bufio"
	"encoding/csv"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"

	"windowfinder/internal/model"
)

func parseTime(s string) (time.Time, error) {
	t, err := time.Parse(time.RFC3339, strings.TrimSpace(s))
	if err != nil {
		return time.Time{}, err
	}
	return t.UTC(), nil
}

func aligned(t time.Time) bool {
	u := t.UTC()
	return u.Second() == 0 && u.Nanosecond() == 0 && u.Minute()%5 == 0
}

func LoadSnapshot(poolsPath, eventsPath, reservationsPath, queriesPath string) (model.Snapshot, error) {
	pools, err := loadPools(poolsPath)
	if err != nil { return model.Snapshot{}, err }
	poolByID := make(map[string]model.Pool, len(pools))
	for _, p := range pools { poolByID[p.ID] = p }
	events, err := loadEvents(eventsPath, poolByID)
	if err != nil { return model.Snapshot{}, err }
	reservations, err := loadReservations(reservationsPath, poolByID)
	if err != nil { return model.Snapshot{}, err }
	queries, err := loadQueries(queriesPath)
	if err != nil { return model.Snapshot{}, err }
	if err := validateBaseline(pools, events, reservations); err != nil { return model.Snapshot{}, err }
	return model.Snapshot{Pools:pools, Events:events, Reservations:reservations, Queries:queries}, nil
}

func loadPools(path string) ([]model.Pool, error) {
	f, err := os.Open(path); if err != nil { return nil, err }; defer f.Close()
	r := csv.NewReader(f); head, err := r.Read(); if err != nil { return nil, err }
	idx, err := columns(head, []string{"pool_id","region","sku","tags","unit_price_micros","base_capacity"}); if err != nil { return nil, err }
	seen := map[string]bool{}; var out []model.Pool
	for rowNo:=2;;rowNo++ {
		row, err := r.Read(); if errors.Is(err, io.EOF) { break }; if err != nil { return nil, fmt.Errorf("pools row %d: %w", rowNo, err) }
		id:=strings.TrimSpace(row[idx["pool_id"]]); region:=strings.TrimSpace(row[idx["region"]]); sku:=strings.TrimSpace(row[idx["sku"]])
		if id=="" || region=="" || sku=="" { return nil, fmt.Errorf("pools row %d: empty identifier", rowNo) }
		if seen[id] { return nil, fmt.Errorf("duplicate pool_id %s", id) }; seen[id]=true
		price, err := strconv.ParseInt(strings.TrimSpace(row[idx["unit_price_micros"]]),10,64); if err!=nil || price<0 { return nil, fmt.Errorf("pool %s: invalid price", id) }
		capv, err := strconv.Atoi(strings.TrimSpace(row[idx["base_capacity"]])); if err!=nil || capv<0 { return nil, fmt.Errorf("pool %s: invalid base capacity", id) }
		tags:=map[string]struct{}{}; for _, t := range strings.Split(strings.TrimSpace(row[idx["tags"]]), "|") { t=strings.TrimSpace(t); if t!="" { tags[t]=struct{}{} } }
		out=append(out, model.Pool{ID:id,Region:region,SKU:sku,Tags:tags,UnitPriceMicros:price,BaseCapacity:capv})
	}
	return out,nil
}

func loadEvents(path string, pools map[string]model.Pool) ([]model.CapacityEvent,error) {
	f,err:=os.Open(path); if err!=nil{return nil,err}; defer f.Close(); r:=csv.NewReader(f); head,err:=r.Read(); if err!=nil{return nil,err}
	idx,err:=columns(head,[]string{"event_id","pool_id","effective_at","delta_units"}); if err!=nil{return nil,err}
	seen:=map[string]model.CapacityEvent{}; var out []model.CapacityEvent
	for rowNo:=2;;rowNo++ { row,err:=r.Read(); if errors.Is(err,io.EOF){break}; if err!=nil{return nil,err}; id:=strings.TrimSpace(row[idx["event_id"]]); pid:=strings.TrimSpace(row[idx["pool_id"]]); if id==""||pid==""{return nil,fmt.Errorf("events row %d: empty id",rowNo)}; if _,ok:=pools[pid];!ok{return nil,fmt.Errorf("event %s: unknown pool",id)}; t,err:=parseTime(row[idx["effective_at"]]); if err!=nil||!aligned(t){return nil,fmt.Errorf("event %s: invalid or unaligned time",id)}; delta,err:=strconv.Atoi(strings.TrimSpace(row[idx["delta_units"]])); if err!=nil||delta==0{return nil,fmt.Errorf("event %s: invalid delta",id)}; e:=model.CapacityEvent{ID:id,PoolID:pid,EffectiveAt:t,DeltaUnits:delta}; if prev,ok:=seen[id];ok{if prev!=e{return nil,fmt.Errorf("event %s: conflicting duplicate",id)};continue}; seen[id]=e; out=append(out,e) }
	return out,nil
}

func loadReservations(path string,pools map[string]model.Pool)([]model.Reservation,error){
	f,err:=os.Open(path);if err!=nil{return nil,err};defer f.Close();r:=csv.NewReader(f);head,err:=r.Read();if err!=nil{return nil,err};idx,err:=columns(head,[]string{"reservation_id","pool_id","start_at","end_at","units"});if err!=nil{return nil,err};seen:=map[string]model.Reservation{};var out []model.Reservation
	for rowNo:=2;;rowNo++{row,err:=r.Read();if errors.Is(err,io.EOF){break};if err!=nil{return nil,err};id:=strings.TrimSpace(row[idx["reservation_id"]]);pid:=strings.TrimSpace(row[idx["pool_id"]]);if id==""||pid==""{return nil,fmt.Errorf("reservations row %d: empty id",rowNo)};if _,ok:=pools[pid];!ok{return nil,fmt.Errorf("reservation %s: unknown pool",id)};s,err1:=parseTime(row[idx["start_at"]]);e,err2:=parseTime(row[idx["end_at"]]);units,err3:=strconv.Atoi(strings.TrimSpace(row[idx["units"]]));if err1!=nil||err2!=nil||!aligned(s)||!aligned(e)||!s.Before(e)||err3!=nil||units<=0{return nil,fmt.Errorf("reservation %s: invalid fields",id)};v:=model.Reservation{ID:id,PoolID:pid,StartAt:s,EndAt:e,Units:units};if prev,ok:=seen[id];ok{if prev!=v{return nil,fmt.Errorf("reservation %s: conflicting duplicate",id)};continue};seen[id]=v;out=append(out,v)}
	return out,nil
}

func loadQueries(path string)([]model.Query,error){
	f,err:=os.Open(path);if err!=nil{return nil,err};defer f.Close();s:=bufio.NewScanner(f);s.Buffer(make([]byte,1024),1024*1024);seen:=map[string]bool{};var out []model.Query;line:=0
	for s.Scan(){line++;raw:=strings.TrimSpace(s.Text());if raw==""{continue};var q model.Query;if err:=json.Unmarshal([]byte(raw),&q);err!=nil{return nil,fmt.Errorf("query line %d: %w",line,err)};if strings.TrimSpace(q.RequestID)==""{return nil,fmt.Errorf("query line %d: empty request_id",line)};if seen[q.RequestID]{return nil,fmt.Errorf("duplicate request_id %s",q.RequestID)};seen[q.RequestID]=true;out=append(out,q)};if err:=s.Err();err!=nil{return nil,err};return out,nil
}

func columns(header []string,required []string)(map[string]int,error){m:=map[string]int{};for i,h:=range header{m[strings.TrimSpace(h)]=i};for _,k:=range required{if _,ok:=m[k];!ok{return nil,fmt.Errorf("missing column %s",k)}};return m,nil}

type delta struct{at time.Time;amount int}

func validateBaseline(pools []model.Pool,events []model.CapacityEvent,reservations []model.Reservation)error{
	byPool:=map[string][]delta{};base:=map[string]int{};for _,p:=range pools{base[p.ID]=p.BaseCapacity};for _,e:=range events{byPool[e.PoolID]=append(byPool[e.PoolID],delta{e.EffectiveAt,e.DeltaUnits})};for _,r:=range reservations{byPool[r.PoolID]=append(byPool[r.PoolID],delta{r.StartAt,-r.Units},delta{r.EndAt,r.Units})}
	for pid,ds:=range byPool{sort.Slice(ds,func(i,j int)bool{return ds[i].at.Before(ds[j].at)});free:=base[pid];for i:=0;i<len(ds);{at:=ds[i].at;sum:=0;j:=i;for j<len(ds)&&ds[j].at.Equal(at){sum+=ds[j].amount;j++};free+=sum;if free<0{return fmt.Errorf("pool %s oversubscribed or negative at %s",pid,at.Format(time.RFC3339))};i=j}}
	return nil
}

func QueryTimes(q model.Query)(time.Time,time.Time,error){s,err1:=parseTime(q.EarliestStart);e,err2:=parseTime(q.LatestFinish);if err1!=nil||err2!=nil||!aligned(s)||!aligned(e){return time.Time{},time.Time{},fmt.Errorf("invalid query times")};return s,e,nil}
