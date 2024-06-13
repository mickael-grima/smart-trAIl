package database

import (
    "fmt"
    "errors"
    "os"
    "log"
    "time"
    "slices"

    "gorm.io/driver/mysql"
    "gorm.io/gorm"
    "gorm.io/gorm/logger"
)

type MySQLDBClient struct {
    db *gorm.DB
}

func InitDb() (*MySQLDBClient, error) {
    env := loadEnv()
    newLogger := logger.New(
        log.New(os.Stdout, "\r\n", log.LstdFlags), // io writer
        logger.Config{
            SlowThreshold:             time.Second, // Slow SQL threshold
            LogLevel:                  logger.Info, // Log level
            IgnoreRecordNotFoundError: true,        // Ignore ErrRecordNotFound error for logger
            ParameterizedQueries:      false,       // Don't include params in the SQL log
            Colorful:                  false,       // Disable color
        },
    )
    db, err := gorm.Open(mysql.Open(env.dsn()), &gorm.Config{
        Logger: newLogger,
    })
    if err != nil {
        return nil, fmt.Errorf("error initializing a MySQL database. Reason: %w", err)
    }
    return &MySQLDBClient{ db: db }, nil
}

func (client *MySQLDBClient) Close() error {
    dbInstance, _ := client.db.DB()
    return dbInstance.Close()
}

// SearchRunners correspond to SQL query:
//   SELECT * FROM runners WHERE first_name LIKE '%{text}%' OR last_name LIKE '%{text}%'
func (client *MySQLDBClient) SearchRunners(text string) ([]Runner, error) {
    var runners []Runner
    err := client.db.Model(&Runner{}).Select("*").
        Where(fmt.Sprintf("first_name LIKE '%%%s%%'", text)).
        Or(fmt.Sprintf("last_name LIKE '%%%s%%'", text)).
        Scan(&runners).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding runners with name like '%%%s%%'. Reason: %w",
            text, err)
    }
    return runners, nil
}

// GetRunner returns the runner corresponding to `id`
func (client *MySQLDBClient) GetRunner(id int) (*Runner, error) {
    var runner Runner
    result := client.db.First(&runner, id)
    if result.Error == nil {
        return &runner, nil
    }
    if errors.Is(result.Error, gorm.ErrRecordNotFound) {
        return nil, nil
    }
    return nil, fmt.Errorf("error querying database. Reason: %w", result.Error)
}

// Get results and competitions related to runnerID
func (client *MySQLDBClient) GetRunnerResults(runnerID int) ([]*CompetitionResult, error) {
    // fetch first results
    results, err := client.getResultsFromRunnerID(runnerID)
    if err != nil { return nil, err }
    if len(results) == 0 { return nil, nil }  // no need to continue if no results

    // fetch events
    events, err := client.getEventsFromResults(results)
    if err != nil { return nil, err }
    if len(events) == 0 { return nil, nil }  // no need to continue if no events

    // map event to its id
    eventsMapping := map[int]*CompetitionEvent{}
    for _, event := range events {
        eventsMapping[event.ID] = event
    }

    // all together
    competitionResults := make([]*CompetitionResult, len(results))
    for i, result := range results {
        competitionResults[i] = &CompetitionResult{ Result: *result }
        event, exists := eventsMapping[result.EventID]
        if exists {
            competitionResults[i].CompetitionEvent = *event
        }
    }

    return competitionResults, nil
}

// SearchCompetitions correspond whose name corresponds has `text` as substring
func (client *MySQLDBClient) SearchEvents(text string) ([]CompetitionEvent, error) {
    var competitions []Competition
    match := fmt.Sprintf("%%%s%%", text)
    err := client.db.
        Preload("CompetitionEvents", "name LIKE ?", match).
        Find(&competitions, "name LIKE ?", match).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding competitions or competition events with name like '%s'. Reason: %w",
            match, err)
    }

    // Gather events together
    var events []CompetitionEvent
    for _, comp := range competitions {
        for _, event := range comp.CompetitionEvents {
            event.Competition = comp
            events = append(events, *event)
        }
    }
    return events, nil
}

// GetCompetition retrieves the competition event corresponding `id`
func (client *MySQLDBClient) GetCompetitionEvent(id int) (*CompetitionEvent, error) {
    var event CompetitionEvent

    // Get event first
    result := client.db.First(&event, id)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return nil, nil
        }
        return nil, fmt.Errorf(
            "error finding event with id=%d. Reason: %w",
            id, result.Error)
    }

    result = client.db.First(&(event.Competition), event.CompetitionID)
    if result.Error != nil {
        if errors.Is(result.Error, gorm.ErrRecordNotFound) {
            return &event, nil
        }
        return nil, fmt.Errorf(
            "error finding competition with id=%d. Reason: %w",
            event.CompetitionID, result.Error)
    }

    return &event, nil
}

func (client *MySQLDBClient) GetCompetitionEventResults(eventID int) ([]*RunnerResult, error) {
    // fetch first results
    results, err := client.getResultsFromEventID(eventID)
    if err != nil { return nil, err }
    if len(results) == 0 { return nil, nil }  // no need to continue if no results

    // fetch then runners
    runners, err := client.getRunnersFromResults(results)
    if err != nil { return nil, err }
    if len(runners) == 0 { return nil, nil }  // no runners: return nothing

    // map runner to its id
    runnersMapping := map[int]*Runner{}
    for _, runner := range runners {
        runnersMapping[runner.ID] = runner
    }

    // all together
    runnerResults := make([]*RunnerResult, len(results))
    for i, result := range results {
        runnerResults[i] = &RunnerResult{ Result: *result }
        runner, exists := runnersMapping[result.RunnerID]
        if exists {
            runnerResults[i].Runner = *runner
        }
    }

    return runnerResults, nil
}

// ----------------------------------------------------------------------------
// -------------------------- Secondary functions -----------------------------
// ----------------------------------------------------------------------------

func (client *MySQLDBClient) getResultsFromRunnerID(runnerID int) ([]*Result, error) {
    var results []*Result
    err := client.db.Find(&results, "runner_id = ?", runnerID).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding results for runer-id=%d. Reason: %w",
            runnerID, err)
    }
    return results, nil
}

func (client *MySQLDBClient) getResultsFromEventID(eventID int) ([]*Result, error) {
    var results []*Result
    err := client.db.Find(&results, "event_id = ?", eventID).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding results for event-id=%d. Reason: %w",
            eventID, err)
    }
    return results, nil
}

func (client *MySQLDBClient) getRunnersFromResults(results []*Result) ([]*Runner, error) {
    // collect IDs first
    var runnerIDs []int
    for _, result := range results {
        runnerIDs = append(runnerIDs, result.RunnerID)
    }

    // call the db
    var runners []*Runner
    err := client.db.Find(&runners, "id IN ?", runnerIDs).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding runners for ids=%d. Reason: %w",
            runnerIDs, err)
    }

    return runners, nil
}

func (client *MySQLDBClient) addCompetitionToEvents(events []*CompetitionEvent) error {
    // collect competition ids
    var competitionIDs []int
    for _, event := range events {
        if slices.Contains(competitionIDs, event.CompetitionID) {
            continue
        }
        competitionIDs = append(competitionIDs, event.CompetitionID)
    }

    // call sql db
    var competitions []*Competition
    err := client.db.Find(&competitions, "id IN ?", competitionIDs).Error
    if err != nil {
        return fmt.Errorf(
            "error finding competitions for ids=%d. Reason: %w",
            competitionIDs, err)
    }

    // add competition to events
    competitionsMapping := map[int]*Competition{}
    for i, _ := range competitions {
        competitionsMapping[competitions[i].ID] = competitions[i]
    }
    for i, _ := range events {
        competition, exists := competitionsMapping[events[i].CompetitionID]
        if !exists {
            continue
        }
        events[i].Competition = *competition
    }
    return nil
}

func (client *MySQLDBClient) getEventsFromResults(results []*Result) ([]*CompetitionEvent, error) {
    // collect event ids
    var eventIDs []int
    for _, result := range results {
        eventIDs = append(eventIDs, result.EventID)
    }

    // call sql db
    var events []*CompetitionEvent
    err := client.db.Find(&events, "id IN ?", eventIDs).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding events for ids=%d. Reason: %w",
            eventIDs, err)
    }

    // if no events, stop here
    if len(events) == 0 {
        return nil, nil
    }

    // add competition fetched from db
    err = client.addCompetitionToEvents(events)

    return events, nil
}
