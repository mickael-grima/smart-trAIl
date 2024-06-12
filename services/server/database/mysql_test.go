package database

import (
    "testing"
    "reflect"
    "fmt"
    "database/sql"
    "time"

    "gorm.io/gorm"
    "gorm.io/driver/mysql"
    "github.com/DATA-DOG/go-sqlmock"
)

// ----------------------------------------------------------------------------
// ------------------------------- Mock Database ------------------------------
// ----------------------------------------------------------------------------

func newMockDB(t *testing.T) (*gorm.DB, sqlmock.Sqlmock) {
    db, mock, err := sqlmock.New()
    if err != nil {
        t.Fatalf("An error '%s' was not expected when opening a stub database connection", err)
    }

    gormDB, err := gorm.Open(mysql.New(mysql.Config{
        Conn:                      db,
        SkipInitializeWithVersion: true,
    }), &gorm.Config{})

    if err != nil {
        t.Fatalf("An error '%s' was not expected when opening gorm database", err)
    }

    return gormDB, mock
}

// ----------------------------------------------------------------------------
// ----------------------------- Test SearchRunners ---------------------------
// ----------------------------------------------------------------------------

func TestMySQLDBClient_SearchRunners_withRunnersExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // runners expected
    rows := sqlmock.NewRows([]string{"id", "first_name", "last_name", "gender"})
    rows.AddRow(1, "John", "Doe", "M")
    rows.AddRow(2, "Sarah", "Smith", "F")
    query := "^SELECT \\* FROM `runners` WHERE first_name LIKE '%test%' OR last_name LIKE '%test%'$"
    mock.ExpectQuery(query).WillReturnRows(rows)

    runners, err := client.SearchRunners("test")
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    expected := []Runner{
        {ID: 1, FirstName: "John", LastName: "Doe", Gender: "M"},
        {ID: 2, FirstName: "Sarah", LastName: "Smith", Gender: "F"},
    }
    if !reflect.DeepEqual(runners, expected) {
        t.Fatalf("Unexpected runners=%v when %v was expected", runners, expected)
    }
}

func TestMySQLDBClient_SearchRunners_withNoRunnersExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // runners expected
    rows := sqlmock.NewRows([]string{"id", "first_name", "last_name", "gender"})
    query := "^SELECT \\* FROM `runners` WHERE first_name LIKE '%test%' OR last_name LIKE '%test%'$"
    mock.ExpectQuery(query).WillReturnRows(rows)

    runners, err := client.SearchRunners("test")
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    var expected []Runner
    if !reflect.DeepEqual(runners, expected) {
        t.Fatalf("Unexpected runners=%v when %v was expected", runners, expected)
    }
}

func TestMySQLDBClient_SearchRunners_error(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // runners expected
    query := "^SELECT \\* FROM `runners` WHERE first_name LIKE '%test%' OR last_name LIKE '%test%'$"
    mock.ExpectQuery(query).WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.SearchRunners("test")
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

// ----------------------------------------------------------------------------
// ------------------------------- Test GetRunner -----------------------------
// ----------------------------------------------------------------------------

func TestMySQLDBClient_GetRunner_withRunnerExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 1 runner expected
    rows := sqlmock.NewRows([]string{"id", "first_name", "last_name", "gender"})
    rows.AddRow(1, "John", "Doe", "M")
    query := "^SELECT (.+) FROM `runners` WHERE `runners`.`id` = (.+)$"
    mock.ExpectQuery(query).WillReturnRows(rows)

    runner, err := client.GetRunner(1)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    expected := &Runner{
        ID: 1,
        FirstName: "John",
        LastName: "Doe",
        Gender: "M",
    }
    if !reflect.DeepEqual(runner, expected) {
        t.Fatalf("Unexpected runner=%v when %v was expected", runner, expected)
    }
}

func TestMySQLDBClient_GetRunner_withNoRunnerExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // No runners expected
    rows := sqlmock.NewRows([]string{"id", "first_name", "last_name", "gender"})
    query := "^SELECT (.+) FROM `runners` WHERE `runners`.`id` = (.+)$"
    mock.ExpectQuery(query).WillReturnRows(rows)

    runner, err := client.GetRunner(1)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    if runner != nil {
        t.Fatalf("Unexpected runner=%v when nil was expected", runner)
    }
}

func TestMySQLDBClient_GetRunner_error(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // Error from the DB
    mock.ExpectQuery("^SELECT (.+) FROM `runners` WHERE `runners`.`id` = (.+)$").
        WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.GetRunner(1)
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

// ----------------------------------------------------------------------------
// --------------------------- Test GetRunnerResults --------------------------
// ----------------------------------------------------------------------------

func TestMySQLDBClient_GetRunnerResults_withRunnerExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 2 results expected
    resultsRows := sqlmock.NewRows([]string{"status", "time", "runner_id"})
    resultsRows.AddRow("finished", sql.NullString{String: "15:04:05", Valid: true}, 13)
    resultsRows.AddRow("abandoned", sql.NullString{Valid: false}, 13)
    query := `^SELECT (.*) FROM \x60results\x60 WHERE runner_id = \?$`
    mock.ExpectQuery(query).WithArgs(13).WillReturnRows(resultsRows)

    results, err := client.GetRunnerResults(13)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    expected := []*Result{
        {Status: "finished", Time: sql.NullString{String: "15:04:05", Valid: true}, RunnerID: 13},
        {Status: "abandoned", Time: sql.NullString{Valid: false}, RunnerID: 13},
    }
    if !reflect.DeepEqual(results, expected) {
        t.Fatalf("Unexpected results=%v when %v was expected.", results, expected)
    }
}

func TestMySQLDBClient_GetRunnerResults_withNoRunnerExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 0 results expected
    resultsRows := sqlmock.NewRows([]string{"status", "time", "runner_id"})
    query := `^SELECT (.*) FROM \x60results\x60 WHERE runner_id = \?$`
    mock.ExpectQuery(query).WithArgs(13).WillReturnRows(resultsRows)

    results, err := client.GetRunnerResults(13)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    expected := []*Result{}
    if !reflect.DeepEqual(results, expected) {
        t.Fatalf("Unexpected results=%v when nil was expected", results)
    }
}

func TestMySQLDBClient_GetRunnerResults_error(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // Error from the DB
    mock.ExpectQuery(`^SELECT (.*) FROM \x60results\x60 WHERE runner_id = \?$`).
        WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.GetRunnerResults(13)
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

// ----------------------------------------------------------------------------
// ------------------------------- SearchEvents -------------------------------
// ----------------------------------------------------------------------------

func TestMySQLDBClient_SearchEvents_withEventsExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    time_, _ := time.Parse(time.DateOnly, "2024-06-07")

    // 1 runner expected
    competitionRows := sqlmock.NewRows([]string{"id", "name", "timekeeper"})
    competitionRows.AddRow(11, "compet", "keeper")
    query := "^SELECT (.+) FROM `competitions` WHERE name LIKE [?]{1}$"
    mock.ExpectQuery(query).WithArgs("%race%").WillReturnRows(competitionRows)

    // 2 results expected
    competitionEventsRows := sqlmock.NewRows([]string{"id", "name", "distance", "start_date", "competition_id"})
    competitionEventsRows.AddRow(111, "Race 1", 32, time_, 11)
    competitionEventsRows.AddRow(112, "Race 2", 52, time_, 11)
    query = "^SELECT (.+) FROM `competition_events` WHERE `competition_events`.`competition_id` = [?]{1} AND name LIKE [?]{1}$"
    mock.ExpectQuery(query).WithArgs(11, "%race%").WillReturnRows(competitionEventsRows)

    events, err := client.SearchEvents("race")
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    competition := Competition{ID: 11, Name: "compet", Timekeeper: "keeper"}
    expected := []CompetitionEvent{
        {ID: 111, Name: "Race 1", Distance: 32, StartDate: time_, CompetitionID: 11, Competition: competition},
        {ID: 112, Name: "Race 2", Distance: 52, StartDate: time_, CompetitionID: 11, Competition: competition},
    }
    // ignore CompetitionEvents in events
    for i, _ := range events {
        events[i].Competition.CompetitionEvents = nil
    }
    if !reflect.DeepEqual(events, expected) {
        t.Fatalf("Unexpected events=%v when %v was expected.", events, expected)
    }
}

func TestMySQLDBClient_SearchEvents_withNoEventsExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // No runners expected
    competitionRows := sqlmock.NewRows([]string{"id", "name", "timekeeper"})
    query := "^SELECT (.+) FROM `competitions` WHERE name LIKE [?]{1}$"
    mock.ExpectQuery(query).WillReturnRows(competitionRows)

    runner, err := client.SearchEvents("race")
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    if runner != nil {
        t.Fatalf("Unexpected runner=%v when nil was expected", runner)
    }
}

func TestMySQLDBClient_SearchEvents_error(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // Error from the DB
    mock.ExpectQuery("^SELECT (.+) FROM `competitions` WHERE name LIKE [?]{1}$").
        WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.SearchEvents("race")
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

// ----------------------------------------------------------------------------
// ---------------------------- GetCompetitionEvent ---------------------------
// ----------------------------------------------------------------------------

func TestMySQLDBClient_GetCompetitionEvent_withEventExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    time_, _ := time.Parse(time.DateOnly, "2024-06-07")

    // 1 event expected
    competitionEventsRows := sqlmock.NewRows([]string{"id", "name", "distance", "start_date", "competition_id"})
    competitionEventsRows.AddRow(111, "Race 1", 32, time_, 11)
    query := `^SELECT (.+) FROM \x60competition_events\x60 WHERE \x60competition_events\x60.\x60id\x60 = \?`
    mock.ExpectQuery(query).WithArgs(111, 1).WillReturnRows(competitionEventsRows)

    // 1 competition expected
    competitionRows := sqlmock.NewRows([]string{"id", "name", "timekeeper"})
    competitionRows.AddRow(11, "compet", "keeper")
    query = `^SELECT (.+) FROM \x60competitions\x60 WHERE \x60competitions\x60.\x60id\x60 = \?`
    mock.ExpectQuery(query).WillReturnRows(competitionRows)

    event, err := client.GetCompetitionEvent(111)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    competition := Competition{ID: 11, Name: "compet", Timekeeper: "keeper"}
    expected := &CompetitionEvent{
        ID: 111,
        Name: "Race 1",
        Distance: 32,
        StartDate: time_,
        CompetitionID: 11,
        Competition: competition,
    }
    // ignore CompetitionEvents in event
    event.Competition.CompetitionEvents = nil
    if !reflect.DeepEqual(event, expected) {
        t.Fatalf("Unexpected event=%v when %v was expected.", event, expected)
    }
}

func TestMySQLDBClient_GetCompetitionEvent_withNoCompetitionExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    time_, _ := time.Parse(time.DateOnly, "2024-06-07")

    // 1 event expected
    competitionEventsRows := sqlmock.NewRows([]string{"id", "name", "distance", "start_date", "competition_id"})
    competitionEventsRows.AddRow(111, "Race 1", 32, time_, 11)
    query := `^SELECT (.+) FROM \x60competition_events\x60 WHERE \x60competition_events\x60.\x60id\x60 = \?`
    mock.ExpectQuery(query).WithArgs(111, 1).WillReturnRows(competitionEventsRows)

    // no competition expected
    competitionRows := sqlmock.NewRows([]string{"id", "name", "timekeeper"})
    query = `^SELECT (.+) FROM \x60competitions\x60 WHERE \x60competitions\x60.\x60id\x60 = \?`
    mock.ExpectQuery(query).WillReturnRows(competitionRows)

    event, err := client.GetCompetitionEvent(111)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    expected := &CompetitionEvent{
        ID: 111,
        Name: "Race 1",
        Distance: 32,
        StartDate: time_,
        CompetitionID: 11,
    }
    if !reflect.DeepEqual(event, expected) {
        t.Fatalf("Unexpected event=%v when %v was expected.", event, expected)
    }
}

func TestMySQLDBClient_GetCompetitionEvent_withNoCompetitionEventExpected(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 1 event expected
    competitionEventsRows := sqlmock.NewRows([]string{"id", "name", "distance", "start_date", "competition_id"})
    query := `^SELECT (.+) FROM \x60competition_events\x60 WHERE \x60competition_events\x60.\x60id\x60 = \?`
    mock.ExpectQuery(query).WithArgs(111, 1).WillReturnRows(competitionEventsRows)

    event, err := client.GetCompetitionEvent(111)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    if event != nil {
        t.Fatalf("Unexpected event=%v when nil was expected", event)
    }
}

func TestMySQLDBClient_GetCompetitionEvent_errorForCompetitionEventFetching(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // Error from the DB
    mock.ExpectQuery("^SELECT (.+) FROM `competitions`").
        WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.GetCompetitionEvent(111)
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

func TestMySQLDBClient_GetCompetitionEvent_errorForCompetitionFetching(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    time_, _ := time.Parse(time.DateOnly, "2024-06-07")

    // 1 event expected
    competitionEventsRows := sqlmock.NewRows([]string{"id", "name", "distance", "start_date", "competition_id"})
    competitionEventsRows.AddRow(111, "Race 1", 32, time_, 11)
    query := `^SELECT (.+) FROM \x60competition_events\x60 WHERE \x60competition_events\x60.\x60id\x60 = \?`
    mock.ExpectQuery(query).WithArgs(111, 1).WillReturnRows(competitionEventsRows)

    // Error from the DB
    mock.ExpectQuery("^SELECT (.+) FROM `competitions`").
        WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.GetCompetitionEvent(111)
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

// ----------------------------------------------------------------------------
// --------------------------- getResultsFromEventID --------------------------
// ----------------------------------------------------------------------------

func TestMySQLDBClient_getResultsFromEventID_withData(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 2 results expected
    resultsRows := sqlmock.NewRows([]string{"status", "time", "event_id", "runner_id"})
    resultsRows.AddRow("finished", sql.NullString{String: "12:34:56", Valid: true}, 111, 12345)
    resultsRows.AddRow("abandoned", sql.NullString{Valid: false}, 111, 23456)
    query := "^SELECT (.*) FROM `results` WHERE event_id = [?]{1}$"
    mock.ExpectQuery(query).WithArgs(111).WillReturnRows(resultsRows)

    // 2 runners expected
    runnersRows := sqlmock.NewRows([]string{"id", "first_name", "last_name", "gender"})
    runnersRows.AddRow(12345, "John", "Boe", "M")
    runnersRows.AddRow(23456, "Alice", "Bob", "F")
    query = `^SELECT (.*) FROM \x60runners\x60 WHERE id IN \(\?,\?\)$`
    mock.ExpectQuery(query).WithArgs(12345, 23456).WillReturnRows(runnersRows)

    results, err := client.GetCompetitionEventResults(111)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }

    expected := []*RunnerResult{
        {
            Result: Result{
                Status: "finished",
                Time: sql.NullString{String: "12:34:56", Valid: true},
                EventID: 111,
                RunnerID: 12345,
            },
            Runner: Runner{
                ID: 12345,
                FirstName: "John",
                LastName: "Boe",
                Gender: "M",
            },
        },
        {
            Result: Result{
                Status: "abandoned",
                Time: sql.NullString{Valid: false},
                EventID: 111,
                RunnerID: 23456,
            },
            Runner: Runner{
                ID: 23456,
                FirstName: "Alice",
                LastName: "Bob",
                Gender: "F",
            },
        },
    }
    if !reflect.DeepEqual(results, expected) {
        t.Fatalf("Unexpected results=%v when %v was expected.", results, expected)
    }
}

func TestMySQLDBClient_getResultsFromEventID_withNoResults(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 2 results expected
    resultsRows := sqlmock.NewRows([]string{"status", "time", "event_id", "runner_id"})
    query := `^SELECT (.*) FROM \x60results\x60 WHERE event_id = \?$`
    mock.ExpectQuery(query).WithArgs(111).WillReturnRows(resultsRows)

    results, err := client.GetCompetitionEventResults(111)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    if results != nil {
        t.Fatalf("Unexpected results=%v when nil was expected.", results)
    }
}

func TestMySQLDBClient_getResultsFromEventID_withNoRunners(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 2 results expected
    resultsRows := sqlmock.NewRows([]string{"status", "time", "event_id", "runner_id"})
    resultsRows.AddRow("finished", sql.NullString{String: "12:34:56", Valid: true}, 111, 12345)
    resultsRows.AddRow("abandoned", sql.NullString{Valid: false}, 111, 23456)
    query := `^SELECT (.*) FROM \x60results\x60 WHERE event_id = \?$`
    mock.ExpectQuery(query).WithArgs(111).WillReturnRows(resultsRows)

    // 2 runners expected
    runnersRows := sqlmock.NewRows([]string{"id", "first_name", "last_name", "gender"})
    query = `^SELECT (.*) FROM \x60runners\x60 WHERE id IN \(\?,\?\)$`
    mock.ExpectQuery(query).WithArgs(12345, 23456).WillReturnRows(runnersRows)

    results, err := client.GetCompetitionEventResults(111)
    if err != nil {
        t.Fatalf("Error: %v", err)
    }
    if results != nil {
        t.Fatalf("Unexpected results=%v when nil was expected.", results)
    }
}

func TestMySQLDBClient_getResultsFromEventID_withResultsFetchingError(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 2 results expected
    query := `^SELECT (.*) FROM \x60results\x60 WHERE event_id = \?$`
    mock.ExpectQuery(query).WithArgs(111).WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.GetCompetitionEventResults(111)
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}

func TestMySQLDBClient_getResultsFromEventID_withRunnersFetchingError(t *testing.T) {
    db, mock := newMockDB(t)
    client := MySQLDBClient{ db: db }
    defer client.Close()

    // 2 results expected
    resultsRows := sqlmock.NewRows([]string{"status", "time", "event_id", "runner_id"})
    resultsRows.AddRow("finished", sql.NullString{String: "12:34:56", Valid: true}, 111, 12345)
    resultsRows.AddRow("abandoned", sql.NullString{Valid: false}, 111, 23456)
    query := `^SELECT (.*) FROM \x60results\x60 WHERE event_id = \?$`
    mock.ExpectQuery(query).WithArgs(111).WillReturnRows(resultsRows)

    // 2 runners expected
    query = `^SELECT (.*) FROM \x60runners\x60 WHERE id IN \(\?,\?\)$`
    mock.ExpectQuery(query).WithArgs(12345, 23456).WillReturnError(fmt.Errorf("ERROR"))

    _, err := client.GetCompetitionEventResults(111)
    if err == nil {
        t.Fatalf("Expecting error but got nothing")
    }
}
