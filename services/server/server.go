package main

import (
    "fmt"
    "net/http"

    "github.com/gorilla/mux"
    log "github.com/sirupsen/logrus"

    "github.com/trail-running/server/database"
)

func router() *mux.Router {
    r := mux.NewRouter()

    // runners endpoints
    r.HandleFunc("/runners/search", searchRunners).Methods("GET")
    r.HandleFunc("/runners/{id:[0-9]+}", getRunner).Methods("GET")
    r.HandleFunc("/runners/{id:[0-9]+}/results", getRunnerResults).Methods("GET")

    // competitions endpoints
    mux.HandleFunc("/events/search", searchEvents).Methods("GET")
    mux.HandleFunc("/events/{id:[0-9]+}", getEvent).Methods("GET")
    mux.HandleFunc("/events/{id:[0-9]+}/results", getEventResults).Methods("GET")

    return r
}

func main {
    // initialize the database client
    db, err = database.InitDb()
    if err != nil {
        log.Fatal(fmt.Sprintf("error by initializing the database client: %v\n", err))
        os.Exit(1)
    }

    // start the server
    err := http.ListenAndServe(":8080", router())
    if errors.Is(err, http.ErrServerClosed) {
        log.Info("server closed\n")
    } else if err != nil {
        log.Fatal(fmt.Sprintf("error starting server: %v\n", err))
        os.Exit(1)
    }
}