package main

import (
    "net/http"
    "encoding/json"

    log "github.com/sirupsen/logrus"

    "github.com/trail-running/server/database"
)

var db database.DBClient

func searchRunners(w http.ResponseWriter, r *http.Request) {
    // check query params
    q := r.URL.Query()
    if q.Get("q") == "" {
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // get runners from the database
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
    // check query params
    q := r.URL.Query()
    if q.Get("id") == "" {
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // get runners from the database
    runner, err := db.GetRunner(q.Get("id"))
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(runner)
}

func getRunnerResults(w http.ResponseWriter, r *http.Request) {
    // check query params
    q := r.URL.Query()
    if q.Get("id") == "" {
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // get results from the database
    runner, err := db.GetRunnerResults(q.Get("id"))
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(runner)
}

func searchEvents(w http.ResponseWriter, r *http.Request) {
    // check query params
    q := r.URL.Query()
    if q.Get("q") == "" {
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // get runners from the database
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
    // check query params
    q := r.URL.Query()
    if q.Get("id") == "" {
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // get runners from the database
    event, err := db.GetCompetitionEvent(q.Get("id"))
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(event)
}

func getEventResults(w http.ResponseWriter, r *http.Request) {
    // check query params
    q := r.URL.Query()
    if q.Get("id") == "" {
        w.WriteHeader(http.StatusBadRequest)
        return
    }

    // get results from the database
    event, err := db.GetCompetitionEventResults(q.Get("id"))
    if err != nil {
        log.Error(err)
        w.WriteHeader(http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(event)
}
