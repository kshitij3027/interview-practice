package main

import (
 "flag"
 "log"
 "net/http"
 "casefold/internal/httpapi"
 "casefold/internal/workspace"
)
func main(){addr:=flag.String("addr",":8080","HTTP listen address");data:=flag.String("data","fixtures/workspace.json","workspace fixture path");flag.Parse();store,err:=workspace.Load(*data);if err!=nil{log.Fatal(err)};log.Printf("CaseFold on %s",*addr);log.Fatal(http.ListenAndServe(*addr,httpapi.New(store)))}
