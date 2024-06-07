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
    db, err := gorm.Open(mysql.Open(env.dsn()), &gorm.Config{})
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
func (client *MySQLDBClient) GetRunnerResults(id int) (*Runner, error) {
    var runner Runner
    result := client.db.Preload("Results").First(&runner, id)
    if result.Error == nil {
        return &runner, nil
    }
    if errors.Is(result.Error, gorm.ErrRecordNotFound) {
        return nil, nil
    }
    return nil, fmt.Errorf("error querying database. Reason: %w", result.Error)
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
        return event, nil
    }
    if errors.Is(result.Error, gorm.ErrRecordNotFound) {
        return nil, nil
    }
    return nil, fmt.Errorf("error querying database. Reason: %w", result.Error)
}
