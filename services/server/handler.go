package main

import (
    "net/http"
    "encoding/json"
    "strconv"

    "github.com/gorilla/mux"
    log "github.com/sirupsen/logrus"

    "github.com/trail-running/server/database"
)

var db database.DBClient

func searchRunners(w http.ResponseWriter, r *http.Request) {
    // get runners from the database
    q := r.URL.Query()
    runners, err := db.SearchRunners(q.Get("q"))
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(runners)
}

func getRunner(w http.ResponseWriter, r *http.Request) {
    // Get id as an integer
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])  // can't result in an error since the router make sure it is an integer

    // get runners from the database
    runner, err := db.GetRunner(id)
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(runner)
}

func getRunnerResults(w http.ResponseWriter, r *http.Request) {
    // Get id as an integer
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])  // can't result in an error since the router make sure it is an integer

    // get results from the database
    results, err := db.GetRunnerResults(id)
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}

func searchEvents(w http.ResponseWriter, r *http.Request) {
    // get runners from the database
    q := r.URL.Query()
    events, err := db.SearchEvents(q.Get("q"))
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(events)
}

func getEvent(w http.ResponseWriter, r *http.Request) {
    // Get id as an integer
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])  // can't result in an error since the router make sure it is an integer

    // get runners from the database
    event, err := db.GetCompetitionEvent(id)
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(event)
}

func getEventResults(w http.ResponseWriter, r *http.Request) {
    // Get id as an integer
    vars := mux.Vars(r)
    id, _ := strconv.Atoi(vars["id"])  // can't result in an error since the router make sure it is an integer

    // get results from the database
    results, err := db.GetCompetitionEventResults(id)
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(results)
}
