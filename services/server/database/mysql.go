package database

import (
    "fmt"
    "errors"
    "os"
    "log"
    "time"

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

// GetRunnerResults fetches the results corresponding to `runner` as a one to many
// relationship
func (client *MySQLDBClient) GetRunnerResults(runnerID int) ([]*Result, error) {
    var results []*Result
    err := client.db.Find(&results, "runner_id = ?", runnerID).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding results for runner-id=%d. Reason: %w",
            runnerID, err)
    }
    return results, nil
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
    var results []*Result
    err := client.db.Find(&results, "event_id = ?", eventID).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding results for event-id=%d. Reason: %w",
            eventID, err)
    }

    if len(results) == 0 {  // no need to continue if no results
        return nil, nil
    }

    // fetch then runners
    var runnerIDs []int
    for _, result := range results {
        runnerIDs = append(runnerIDs, result.RunnerID)
    }
    var runners []*Runner
    err = client.db.Find(&runners, "id IN ?", runnerIDs).Error
    if err != nil {
        return nil, fmt.Errorf(
            "error finding runners for event-id=%d. Reason: %w",
            eventID, err)
    }

    // no runners: return nothing
    if len(runners) == 0 {
        return nil, nil
    }

    // all together
    runnerResultMapping := make(map[int]*RunnerResult, 0)
    for _, result := range results {
        runnerResultMapping[result.RunnerID] = &RunnerResult{ Result: *result }
    }
    for _, runner := range runners {
        _, exists := runnerResultMapping[runner.ID]
        if exists {
            runnerResultMapping[runner.ID].Runner = *runner
        }
    }

    // transform to list
    var runnerResults []*RunnerResult
    for _, res := range runnerResultMapping {
        runnerResults = append(runnerResults, res)
    }

    return runnerResults, nil
}
