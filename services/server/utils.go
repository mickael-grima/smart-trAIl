package main

import (
    "io"

    log "github.com/sirupsen/logrus"
)

func closeOrLog(c io.Closer) {
    if err := c.Close(); err != nil {
        log.Errorf("error closing %v. Reason: %v", c, err)
    }
}
