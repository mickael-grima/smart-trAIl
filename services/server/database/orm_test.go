package database

import (
    "testing"
    "encoding/json"
    "reflect"
    "database/sql"
    "time"
)

func parseDate(str string) time.Time {
    time_, _ := time.Parse(time.DateOnly, str)
    return time_
}

func TestMarshallJSON(t *testing.T) {
    testCases := []struct{
        name     string
        data     any
        expected []byte
    }{
        {
            name: "runner-without-birth-nor-results",
            data: &Runner{
                ID: 1234,
                FirstName: "John",
                LastName: "Boe",
                Gender: "M",
            },
            expected: []byte(`{"first_name":"John","gender":"M","id":1234,"last_name":"Boe"}`),
        },
        {
            name: "runner-with-birth-but-without-results",
            data: &Runner{
                ID: 1234,
                FirstName: "John",
                LastName: "Boe",
                Gender: "M",
                BirthYear: sql.NullInt16{Int16: 1991, Valid: true},
            },
            expected: []byte(`{"birth_year":1991,"first_name":"John","gender":"M","id":1234,"last_name":"Boe"}`),
        },
        {
            name: "runner-with-birth-with-results",
            data: &Runner{
                ID: 1234,
                FirstName: "John",
                LastName: "Boe",
                Gender: "M",
                BirthYear: sql.NullInt16{Int16: 1991, Valid: true},
                Results: []*Result{
                    {
                        Status: "finished",
                        Category: sql.NullString{String:"SEH", Valid: true},
                        ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
                    },
                    {
                        Status: "abandoned",
                        Category: sql.NullString{String: "M1H", Valid: true},
                    },
                },
            },
            expected: []byte(`{"birth_year":1991,"first_name":"John","gender":"M","id":1234,"last_name":"Boe","results":[{"category":"SEH","ranking":{"scratch":13},"status":"finished"},{"category":"M1H","status":"abandoned"}]}`),
        },
        {
            name: "result-with-one-ranking",
            data: &Result{
                Status: "finished",
                Category: sql.NullString{String:"SEH", Valid: true},
                ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
            },
            expected: []byte(`{"category":"SEH","ranking":{"scratch":13},"status":"finished"}`),
        },
        {
            name: "result-with-all-rankings",
            data: &Result{
                Status: "finished",
                Category: sql.NullString{String:"SEH", Valid: true},
                ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
                GenderRanking: sql.NullInt32{Int32: 13, Valid: true},
                CategoryRanking: sql.NullInt32{Int32: 5, Valid: true},
            },
            expected: []byte(`{"category":"SEH","ranking":{"category":5,"gender":13,"scratch":13},"status":"finished"}`),
        },
        {
            name: "result-with-everything",
            data: &Result{
                Status: "finished",
                Time: sql.NullString{String: "32:54:19", Valid: true},
                License: sql.NullString{String:"license", Valid: true},
                Category: sql.NullString{String:"SEH", Valid: true},
                ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
                GenderRanking: sql.NullInt32{Int32: 13, Valid: true},
                CategoryRanking: sql.NullInt32{Int32: 5, Valid: true},
            },
            expected: []byte(`{"category":"SEH","license":"license","ranking":{"category":5,"gender":13,"scratch":13},"status":"finished","time":"32:54:19"}`),
        },
        {
            name: "result-without-ranking",
            data: &Result{
                Status: "abandoned",
                Category: sql.NullString{String: "M1H", Valid: true},
            },
            expected: []byte(`{"category":"M1H","status":"abandoned"}`),
        },
        {
            name: "runnerresult-without-ranking",
            data: &RunnerResult{
                Result: Result{
                    Status: "abandoned",
                    Category: sql.NullString{String: "M1H", Valid: true},
                },
                Runner: Runner{
                    ID: 23456,
                    FirstName: "Alice",
                    LastName: "Bob",
                    Gender: "F",
                },
            },
            expected: []byte(`{"category":"M1H","first_name":"Alice","gender":"F","last_name":"Bob","runner_id":23456,"status":"abandoned"}`),
        },
        {
            name: "runnerresult-with-everything",
            data: &RunnerResult{
                Result: Result{
                    Status: "finished",
                    Time: sql.NullString{String: "32:54:19", Valid: true},
                    License: sql.NullString{String:"license", Valid: true},
                    Category: sql.NullString{String:"SEH", Valid: true},
                    ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
                    GenderRanking: sql.NullInt32{Int32: 13, Valid: true},
                    CategoryRanking: sql.NullInt32{Int32: 5, Valid: true},
                },
                Runner: Runner{
                    ID: 12345,
                    FirstName: "John",
                    LastName: "Boe",
                    Gender: "M",
                    Results: []*Result{
                        {
                            Status: "finished",
                            Time: sql.NullString{String: "32:54:19", Valid: true},
                            License: sql.NullString{String:"license", Valid: true},
                            Category: sql.NullString{String:"SEH", Valid: true},
                            ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
                            GenderRanking: sql.NullInt32{Int32: 13, Valid: true},
                            CategoryRanking: sql.NullInt32{Int32: 5, Valid: true},
                        },
                    },
                },
            },
            expected: []byte(`{"category":"SEH","first_name":"John","gender":"M","last_name":"Boe","license":"license","ranking":{"category":5,"gender":13,"scratch":13},"runner_id":12345,"status":"finished","time":"32:54:19"}`),
        },
        {
            name: "competition-without-events",
            data: &Competition{
                ID: 11,
                Name: "compet",
                Timekeeper: "keeper",
            },
            expected: []byte(`{"id":11,"name":"compet","timekeeper":"keeper"}`),
        },
        {
            name: "competition-with-events",
            data: &Competition{
                ID: 11,
                Name: "compet",
                Timekeeper: "keeper",
                CompetitionEvents: []*CompetitionEvent{
                    {
                        ID: 111,
                        CompetitionID: 11,
                        Name: "event1",
                        Distance: 32,
                        StartDate: parseDate("2024-06-07"),
                    },
                },
            },
            expected: []byte(`{"id":11,"name":"compet","timekeeper":"keeper"}`),
        },
        {
            name: "competition-event-without-competition-and-results",
            data: &CompetitionEvent{
                ID: 111,
                CompetitionID: 11,
                Name: "event",
                Distance: 32,
                StartDate: parseDate("2024-06-07"),
            },
            expected: []byte(`{"distance":32,"id":111,"name":"event","start_date":"2024-06-07"}`),
        },
        {
            name: "competition-event-with-everything",
            data: &CompetitionEvent{
                ID: 111,
                CompetitionID: 11,
                Name: "event",
                Distance: 32,
                StartDate: parseDate("2024-06-07"),
                EndDate: sql.NullTime{Time: parseDate("2024-06-08"), Valid: true},
                Competition: Competition{
                    ID: 11,
                    Name: "compet",
                    Timekeeper: "keeper",
                },
                Results: []*RunnerResult{
                    {
                        Runner: Runner{
                            ID: 12345,
                            FirstName: "John",
                            LastName: "Boe",
                            Gender: "M",
                        },
                        Result: Result{
                            Status: "finished",
                            Time: sql.NullString{String: "32:54:19", Valid: true},
                            License: sql.NullString{String:"license", Valid: true},
                            Category: sql.NullString{String:"SEH", Valid: true},
                            ScratchRanking: sql.NullInt32{Int32: 13, Valid: true},
                            GenderRanking: sql.NullInt32{Int32: 13, Valid: true},
                            CategoryRanking: sql.NullInt32{Int32: 5, Valid: true},
                        },
                    },
                    {
                        Runner: Runner{
                            ID: 23456,
                            FirstName: "Alice",
                            LastName: "Bob",
                            Gender: "F",
                        },
                        Result: Result{
                            Status: "abandoned",
                            Category: sql.NullString{String:"M1F", Valid: true},
                        },
                    },
                },
            },
            expected: []byte(`{"competition":{"id":11,"name":"compet","timekeeper":"keeper"},"distance":32,"end_date":"2024-06-08","id":111,"name":"event","results":[{"category":"SEH","first_name":"John","gender":"M","last_name":"Boe","license":"license","ranking":{"category":5,"gender":13,"scratch":13},"runner_id":12345,"status":"finished","time":"32:54:19"},{"category":"M1F","first_name":"Alice","gender":"F","last_name":"Bob","runner_id":23456,"status":"abandoned"}],"start_date":"2024-06-07"}`),
        },
    }

    for _, testCase := range testCases {
        t.Run(testCase.name, func(tt *testing.T) {
            b, err := json.Marshal(testCase.data)
            if err != nil {
                tt.Fatalf("Unexpected error=%v", err)
            }
            if !reflect.DeepEqual(b, testCase.expected) {
                tt.Fatalf("Unexpected output=%s, when %s was expected", string(b), string(testCase.expected))
            }
        })
    }
}
