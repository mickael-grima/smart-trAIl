package database

import (
    "fmt"
    "errors"

    "gorm.io/driver/mysql"
    "gorm.io/gorm"
)

type MySQLDBClient struct {
    db *gorm.DB
}

func InitDb() (*MySQLDBClient, error) {
    env := loadEnv()
    db, err := gorm.Open(mysql.Open(dsn), &gorm.Config{})
    if err != nil {
        return nil, fmt.Errorf("error initializing a MySQL database. Reason: %w", err)
    }
    return &MySQLDBClient{ db: db }, nil
}

// SearchRunners correspond to SQL query:
//   SELECT * FROM runners WHERE first_name LIKE '%{text}%' OR last_name LIKE '%{text}%'
func (client *MySQLDBClient) SearchRunners(text string) ([]Runner, error) {
    var runners []Runner
    likeString := fmt.Sprintf("%%%s%%", text)
    result := client.db
        .Where("first_name LIKE ? OR last_name LIKE ?", likeString, likeString)
        .Find(&runners)
    if result.Error == nil {
        return runners, nil
    }
    if errors.Is(result.Error, gorm.ErrRecordNotFound) {
        return runners, nil
    }
    return nil, fmt.Errorf("error querying database. Reason: %w", result.Error)
}

// GetRunner returns the runner corresponding to `id`
func (client *MySQLDBClient) GetRunner(id int) (*Runner, error) {
    var runner Runner
    result := client.db.First(&user, id)
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
func (client *MySQLDBClient) GetRunnerResults(id int) (*Runner, error) {
    runner := &Runner{ID: id}
    err := client.db.Preload("results").Find(runner).Error
    if err != nil {
        return nil, fmt.Errorf("Error getting results for runner.id=%d. Reason=%w", id, err)
    }
    return runner, nil
}

// SearchCompetitions correspond to SQL query:
//   SELECT * FROM competitions JOIN competitionEvents ON competitions.id = competition_id
//   WHERE competitions.name LIKE '%{text}%' OR competitionEvents.name LIKE '%{text}%'
func (client *MySQLDBClient) SearchEvents(text string) ([]CompetitionEvent, error) {
    var competitions []Competition
    err := client.db
        .Preload("competitionEvents")
        .Find(&competitions)
        .Where(fmt.Sprintf("competitions.name LIKE '%%%s%%'", text))
        .Or(fmt.Sprintf("competitionEvents.name LIKE '%%%s%%'", text)); err != nil
    if err != nil {
        return fmt.Errorf(
        "error finding competitions or competition events with name like '%%%s%%'. Reason: %w",
        text, err)
    }

    // Gather events together
    var events []CompetitionEvent
    for _, comp := range competitions {
        for _, event := range comp.Events {
            events = append(events, event)
        }
    }
    return events
}

// GetCompetition retrieves the competition event corresponding `id`
func (client *MySQLDBClient) GetCompetitionEvent(id int) (*CompetitionEvent, error) {
    var event CompetitionEvent
    result := client.db.Preload("Competitions").First(&event, id)
    if result.Error == nil {
        return &event, nil
    }
    if errors.Is(result.Error, gorm.ErrRecordNotFound) {
        return nil, nil
    }
    return nil, fmt.Errorf("error querying database. Reason: %w", result.Error)
}

// GetCompetitionResults
func (client *MySQLDBClient) GetCompetitionEventResults(id int) (*CompetitionEvent, error) {
    event := &CompetitionEvent{ID: id}
    result := client.db.Preload("Results").First(&event, id)
    if result.Error == nil {
        return &event, nil
    }
    if errors.Is(result.Error, gorm.ErrRecordNotFound) {
        return nil, nil
    }
    return nil, fmt.Errorf("error querying database. Reason: %w", result.Error)
}
