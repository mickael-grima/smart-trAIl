package database

import (
    "database/sql"
    "time"
    "encoding/json"
)

type Runner struct {
    ID        int
    FirstName string         `gorm:"not null,varchar(255)"`
    LastName  string         `gorm:"not null,varchar(255)"`
    Gender    string         `gorm:"not null,char(1)"`
    BirthYear sql.NullInt16
    Results   []*Result
}

func (r *Runner) toMap() map[string]any {
    data := map[string]any{
        "id": r.ID,
        "first_name": r.FirstName,
        "last_name": r.LastName,
        "gender": r.Gender,
    }
    if r.BirthYear.Valid {
        data["birth_year"] = r.BirthYear.Int16
    }
    if len(r.Results) > 0 {
        data["results"] = r.Results
    }
    return data
}

func (r *Runner) MarshalJSON() ([]byte, error) {
	return json.Marshal(r.toMap())
}

type Competition struct {
    ID                int                 `json:"id"`
    Name              string              `gorm:"not null,varchar(255)" json:"name"`
    Timekeeper        string              `gorm:"not null,varchar(50)" json:"timekeeper"`
    CompetitionEvents []*CompetitionEvent `json:"-"`
}

type CompetitionEvent struct {
    ID            int             `json:"id"`
    CompetitionID int             `json:"-"`
    Name          string          `gorm:"not null,varchar(255)" json:"name"`
    Distance      uint            `gorm:"not null,smallint,unsigned" json:"distance"`
    StartDate     time.Time       `gorm:"not null" json:"start_date"`
    EndDate       sql.NullTime    `json:"end_date,omitempty"`
    Competition   Competition     `gorm:"foreignKey:CompetitionID" json:"competition"`
    Results       []*RunnerResult `gorm:"foreignKey:EventID" json:"runners,omitempty"`
}

func (e *CompetitionEvent) toMap() map[string]any {
    data := map[string]any{
        "id": e.ID,
        "name": e.Name,
        "distance": e.Distance,
        "start_date": e.StartDate.Format(time.DateOnly),
    }
    if e.EndDate.Valid {
        data["end_date"] = e.EndDate.Time.Format(time.DateOnly)
    }
    if e.Competition.ID > 0 {
        data["competition"] = e.Competition
    }
    if len(e.Results) > 0 {
        data["results"] = e.Results
    }
    return data
}

func (e *CompetitionEvent) MarshalJSON() ([]byte, error) {
	return json.Marshal(e.toMap())
}

type Result struct {
    RunnerID           int            `json:"-"`
    EventID            int            `gorm:"" json:"-"`
    Status             string         `gorm:"not null,varchar(20)" json:"status"`
    Time               sql.NullString `json:"time,omitempty"`
    License            sql.NullString `gorm:"varchar(255)" json:"license,omitempty"`
    Category           sql.NullString `gorm:"varchar(20)" json:"category,omitempty"`
    ScratchRanking     sql.NullInt32  `gorm:"smallint,unsigned" json:"scratch_ranking,omitempty"`
    GenderRanking      sql.NullInt32  `gorm:"smallint,unsigned" json:"gender_ranking,omitempty"`
    CategoryRanking    sql.NullInt32  `gorm:"smallint,unsigned" json:"category_ranking,omitempty"`
}

func (r *Result) toMap() map[string]any {
    data := map[string]any{
        "status": r.Status,
    }
    if r.Time.Valid {
        data["time"] = r.Time.String
    }
    if r.License.Valid {
        data["license"] = r.License.String
    }
    if r.Category.Valid {
        data["category"] = r.Category.String
    }
    if r.ScratchRanking.Valid || r.GenderRanking.Valid || r.CategoryRanking.Valid {
        ranking := map[string]any{}
        if r.ScratchRanking.Valid {
            ranking["scratch"] = r.ScratchRanking.Int32
        }
        if r.GenderRanking.Valid {
            ranking["gender"] = r.GenderRanking.Int32
        }
        if r.CategoryRanking.Valid {
            ranking["category"] = r.CategoryRanking.Int32
        }
        data["ranking"] = ranking
    }
    return data
}

func (r *Result) MarshalJSON() ([]byte, error) {
	return json.Marshal(r.toMap())
}

type RunnerResult struct {
    Result
    Runner
}

func (r *RunnerResult) toMap() map[string]any {
    data := r.Result.toMap()
    for key, value := range r.Runner.toMap() {
        switch key {
        case "id":  // convert to runner_id
            data["runner_id"] = value
        case "results":  // skip it
            continue
        default:
            data[key] = value
        }
    }
    return data
}

func (r *RunnerResult) MarshalJSON() ([]byte, error) {
	return json.Marshal(r.toMap())
}

type CompetitionResult struct {
    Result
    CompetitionEvent
}

func (r *CompetitionResult) toMap() map[string]any {
    data := r.Result.toMap()
    for key, value := range r.CompetitionEvent.toMap() {
        switch key {
        case "id":  // convert to event_id
            data["event_id"] = value
        case "name":  // convert to event_name
            data["event_name"] = value
        case "results":  // skip it
            continue
        default:
            data[key] = value
        }
    }
    return data
}

func (r *CompetitionResult) MarshalJSON() ([]byte, error) {
	return json.Marshal(r.toMap())
}
