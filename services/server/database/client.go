package database

import (
    "io"
)

type DBClient interface {
    io.Closer

    // Runners related
    SearchRunners(text string) ([]*Runner, error)
    GetRunner(id int) (*Runner, error)
    GetRunnerResults(runnerID int) ([]*CompetitionResult, error)

    // Runners related
    SearchEvents(text string) ([]*CompetitionEvent, error)
    GetCompetitionEvent(id int) (*CompetitionEvent, error)
    GetCompetitionEventResults(eventID int) ([]*RunnerResult, error)
}
