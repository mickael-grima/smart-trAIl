package database

import (
    "database/sql"
)

type Runner struct {
    ID        int         `json:"id"`
    FirstName string      `gorm:"not null,varchar(255)" json:"first_name"`
    LastName  string      `gorm:"not null,varchar(255)" json:"last_name"`
    Gender    string      `gorm:"not null,char(1)" json:"gender"`
    BirthYear sql.NullInt `json:"birth_year,omitempty"`
    Results   []Result    `json:"results.omitempty"`
}

type Competition struct {
    ID         int     `json:"id"`
    Name       string  `gorm:"not null,varchar(255)" json:"name"`
    Timekeeper string  `gorm:"not null,varchar(50)" json:"timekeeper"`
    Events     []Event `gorm:"foreignKey:CompetitionID" json:"events,omitempty"`
}

type CompetitionEvent struct {
    ID            int          `json:"id"`
    Name          string       `gorm:"not null,varchar(255)" json:"name"`
    Distance      uint         `gorm:"not null,smallint,unsigned" json:"distance"`
    StartDate     time.Date    `gorm:"not null" json:"start_date"`
    EndDate       sql.NullDate `json:"end_date,omitempty"`
    CompetitionID int          `json:"-"`
    Competition   Competition  `json:"competition"`
    Results       []Result     `gorm:"foreignKey:EventID" json:"results,omitempty"`
}

type Result struct {
    EventID          int              `json:"-"`
    RunnerID         int              `json:"-"`
    Status           string           `gorm:"not null,varchar(20)" json:"status"`
    Time             sql.NullTime     `json:"time,omitempty"`
    License          sql.NullString   `gorm:"varchar(255)" json:"license,omitempty"`
    Category         sql.NullString   `gorm:"varchar(20)" json:"category,omitempty"`
    ScratchRanking   sql.NullUInt     `gorm:"smallint,unsigned" json:"scratch_ranking,omitempty"`
    GenderRanking    sql.NullUInt     `gorm:"smallint,unsigned" json:"gender_ranking,omitempty"`
    CategoryRanking  sql.NullUInt     `gorm:"smallint,unsigned" json:"category_ranking,omitempty"`
}
