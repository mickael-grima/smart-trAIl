package database

import (
    "io"
)

type DBClient interface {
    io.Closer

    // Runners related
    SearchRunners(text string) ([]Runner, error)
    GetRunner(id int) (*Runner, error)
    GetRunnerResults(id int) (*Runner, error)

    // Runners related
    SearchEvents(text string) ([]CompetitionEvent, error)
    GetCompetitionEvent(id int) (*CompetitionEvent, error)
    GetCompetitionEventResults(id int) (*CompetitionEvent, error)
}
