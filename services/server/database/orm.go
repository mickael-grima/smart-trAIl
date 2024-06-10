package database

import (
    "database/sql"
    "time"
)

type Runner struct {
    ID        int            `json:"id"`
    FirstName string         `gorm:"not null,varchar(255)" json:"first_name"`
    LastName  string         `gorm:"not null,varchar(255)" json:"last_name"`
    Gender    string         `gorm:"not null,char(1)" json:"gender"`
    BirthYear sql.NullInt16  `json:"birth_year,omitempty"`
    Results   []*Result      `json:"results,omitempty"`
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

type Result struct {
    RunnerID           int            `json:"-"`
    EventID            int            `gorm:"" json:"-"`
    Status             string         `gorm:"not null,varchar(20)" json:"status"`
    Time               sql.NullTime   `json:"time,omitempty"`
    License            sql.NullString `gorm:"varchar(255)" json:"license,omitempty"`
    Category           sql.NullString `gorm:"varchar(20)" json:"category,omitempty"`
    ScratchRanking     sql.NullInt32  `gorm:"smallint,unsigned" json:"scratch_ranking,omitempty"`
    GenderRanking      sql.NullInt32  `gorm:"smallint,unsigned" json:"gender_ranking,omitempty"`
    CategoryRanking    sql.NullInt32  `gorm:"smallint,unsigned" json:"category_ranking,omitempty"`
}

type RunnerResult struct {
    Result
    Runner
}
