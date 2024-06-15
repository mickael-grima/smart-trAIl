package main

import (
    "fmt"
    "os"
    "net/http"
    "errors"

    "github.com/gorilla/mux"
    "github.com/gorilla/handlers"
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
    r.HandleFunc("/events/search", searchEvents).Methods("GET")
    r.HandleFunc("/events/{id:[0-9]+}", getEvent).Methods("GET")
    r.HandleFunc("/events/{id:[0-9]+}/results", getEventResults).Methods("GET")

    return r
}

func main() {
    var err error

    // initialize the database client
    db, err = database.InitDb()
    if err != nil {
        log.Fatal(fmt.Sprintf("error by initializing the database client: %v\n", err))
        os.Exit(1)
    }
    defer closeOrLog(db)

    // start the server
    handler := handlers.LoggingHandler(os.Stdout, handlers.CompressHandler(router()))
    err = http.ListenAndServe(":8080", handler)
    if errors.Is(err, http.ErrServerClosed) {
        log.Info("server closed\n")
    } else if err != nil {
        log.Fatal(fmt.Sprintf("error starting server: %v\n", err))
        os.Exit(1)
    }
}