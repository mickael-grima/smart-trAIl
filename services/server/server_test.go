package main

import (
    "testing"
    "fmt"
    "net/http"
    "net/http/httptest"
    "strings"

    "github.com/trail-running/server/database"
)

// ----------------------------------------------------------------------------
// ------------------------------- Mock Database ------------------------------
// ----------------------------------------------------------------------------

type MockDatabase struct {
    returnError bool  // If true, returns systematically an error

    runners        map[int]database.Runner   // Map runners with their ids
    runnersResults map[int][]database.Result // Map runner's results with runner's id

    events        map[int]database.CompetitionEvent // Map events with their ids
    eventsResults map[int][]database.RunnerResult   // Map events' runners with event's id
}

func (db *MockDatabase) Close() error { return nil }

func (db *MockDatabase) SearchRunners(text string) ([]database.Runner, error) {
    if db.returnError {
        return nil, fmt.Errorf("ERROR")
    }
    runners := make([]database.Runner, 0)
    for _, runner := range db.runners {
        if (strings.Contains(runner.FirstName, text) || strings.Contains(runner.LastName, text)) {
            runners = append(runners, runner)
        }
    }
    return runners, nil
}

func (db *MockDatabase) GetRunner(id int) (*database.Runner, error) {
    if db.returnError {
        return nil, fmt.Errorf("ERROR")
    }
    runner, exists := db.runners[id]
    if exists {
        return &runner, nil
    }
    return nil, fmt.Errorf("No runner with id=%d", id)
}

func (db *MockDatabase) GetRunnerResults(runnerID int) ([]*database.Result, error) {
    if db.returnError {
        return nil, fmt.Errorf("ERROR")
    }
    results := make([]*database.Result, len(db.runnersResults[runnerID]))
    for i, _ := range db.runnersResults[runnerID] {
        results = append(results, &(db.runnersResults[runnerID][i]))
    }
    return results, nil
}

func (db *MockDatabase) SearchEvents(text string) ([]database.CompetitionEvent, error) {
    if db.returnError {
        return nil, fmt.Errorf("ERROR")
    }
    events := make([]database.CompetitionEvent, 0)
    for _, event := range db.events {
        if (strings.Contains(event.Name, text)) {
            events = append(events, event)
        }
    }
    return events, nil
}

func (db *MockDatabase) GetCompetitionEvent(id int) (*database.CompetitionEvent, error) {
    if db.returnError {
        return nil, fmt.Errorf("ERROR")
    }
    event, exists := db.events[id]
    if exists {
        return &event, nil
    }
    return nil, fmt.Errorf("No event with id=%d", id)
}

func (db *MockDatabase) GetCompetitionEventResults(eventID int) ([]*database.RunnerResult, error) {
    if db.returnError {
        return nil, fmt.Errorf("ERROR")
    }
    results := make([]*database.RunnerResult, len(db.eventsResults[eventID]))
    for i, _ := range db.eventsResults[eventID] {
        results = append(results, &(db.eventsResults[eventID][i]))
    }
    return results, nil
}

func mockDB(returnError bool) *MockDatabase {
    return &MockDatabase{
        returnError: returnError,
        runners: map[int]database.Runner{
            12345: database.Runner{
                ID: 12345,
                FirstName: "John",
                LastName: "Boe",
                Gender: "M",
            },
            23456: database.Runner{
                ID: 23456,
                FirstName: "Alice",
                LastName: "Bob",
                Gender: "F",
            },
        },
        runnersResults: map[int][]database.Result{
            12345: []database.Result{
                {Status: "finisher"},
                {Status: "not started"},
            },
            23456: []database.Result{},
        },
        events: map[int]database.CompetitionEvent{
            111: database.CompetitionEvent{
                ID: 111,
                Name: "run1",
                Distance: 12,
            },
            222: database.CompetitionEvent{
                ID: 222,
                Name: "run2",
                Distance: 36,
            },
        },
        eventsResults: map[int][]database.RunnerResult{
            111: []database.RunnerResult{
                {
                    Result: database.Result{Status: "finisher"},
                    Runner: database.Runner{FirstName: "John", LastName: "Boe"},
                },
                {
                    Result: database.Result{Status: "abandoned"},
                    Runner: database.Runner{FirstName: "Alice", LastName: "Bob"},
                },
            },
            222: []database.RunnerResult{},
        },
    }
}

// ----------------------------------------------------------------------------
// ------------------------------ Test Functions ------------------------------
// ----------------------------------------------------------------------------

func Test_Endpoints(t *testing.T) {
    testCases := []struct{
        name             string
        method           string
        endpoint         string
        dbError          bool
        expectedStatus   int
        expectedResponse string
    }{
        // /runners/search
        {
            name: "search-runners-failing-db",
            method: "GET",
            endpoint: "/runners/search?q=test",
            dbError: true,
            expectedStatus: http.StatusInternalServerError,
        },
        {
            name: "search-runners-no-query",
            method: "GET",
            endpoint: "/runners/search",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        {
            name: "search-runners-with-query",
            method: "GET",
            endpoint: "/runners/search?q=bo",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        // /runners/<id>
        {
            name: "get-runner-failing-db",
            method: "GET",
            endpoint: "/runners/12345",
            dbError: true,
            expectedStatus: http.StatusInternalServerError,
            expectedResponse: "",
        },
        {
            name: "get-runner-missing-id",
            method: "GET",
            endpoint: "/runners/",
            dbError: false,
            expectedStatus: http.StatusNotFound,
            expectedResponse: "",
        },
        {
            name: "get-runner-wrong-id",
            method: "GET",
            endpoint: "/runners/aftsg",
            dbError: false,
            expectedStatus: http.StatusNotFound,
            expectedResponse: "",
        },
        {
            name: "get-runner-with-id",
            method: "GET",
            endpoint: "/runners/12345",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        // /runners/<id>/results
        {
            name: "get-runner-results-failing-db",
            method: "GET",
            endpoint: "/runners/12345/results",
            dbError: true,
            expectedStatus: http.StatusInternalServerError,
            expectedResponse: "",
        },
        {
            name: "get-runner-results-wrong-id",
            method: "GET",
            endpoint: "/runners/jkghgf/results",
            dbError: false,
            expectedStatus: http.StatusNotFound,
            expectedResponse: "",
        },
        {
            name: "get-runner-results-with-id",
            method: "GET",
            endpoint: "/runners/12345/results",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        // /events/search
        {
            name: "search-events-failing-db",
            method: "GET",
            endpoint: "/events/search?q=test",
            dbError: true,
            expectedStatus: http.StatusInternalServerError,
        },
        {
            name: "search-events-no-query",
            method: "GET",
            endpoint: "/events/search",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        {
            name: "search-events-with-query",
            method: "GET",
            endpoint: "/events/search?q=run",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        // /events/<id>
        {
            name: "get-events-failing-db",
            method: "GET",
            endpoint: "/events/111",
            dbError: true,
            expectedStatus: http.StatusInternalServerError,
            expectedResponse: "",
        },
        {
            name: "get-events-missing-id",
            method: "GET",
            endpoint: "/events/",
            dbError: false,
            expectedStatus: http.StatusNotFound,
            expectedResponse: "",
        },
        {
            name: "get-events-wrong-id",
            method: "GET",
            endpoint: "/events/aftsg",
            dbError: false,
            expectedStatus: http.StatusNotFound,
            expectedResponse: "",
        },
        {
            name: "get-events-with-id",
            method: "GET",
            endpoint: "/events/111",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
        // /events/<id>/results
        {
            name: "get-events-results-failing-db",
            method: "GET",
            endpoint: "/events/111/results",
            dbError: true,
            expectedStatus: http.StatusInternalServerError,
            expectedResponse: "",
        },
        {
            name: "get-events-results-wrong-id",
            method: "GET",
            endpoint: "/events/jkghgf/results",
            dbError: false,
            expectedStatus: http.StatusNotFound,
            expectedResponse: "",
        },
        {
            name: "get-events-results-with-id",
            method: "GET",
            endpoint: "/events/111/results",
            dbError: false,
            expectedStatus: http.StatusOK,
            expectedResponse: "",
        },
    }

    for _, testCase := range testCases {
        m := router()
        t.Run(testCase.name, func(tt *testing.T) {
            db = mockDB(testCase.dbError)
            defer db.Close()

            req := httptest.NewRequest(testCase.method, testCase.endpoint, nil)
            w := httptest.NewRecorder()

            // Call the server
            m.ServeHTTP(w, req)

            // tests
            if (w.Code != testCase.expectedStatus) {
                tt.Fatal("Server error: Returned ", w.Code, " instead of ", testCase.expectedStatus)
            }
        })
    }
}
