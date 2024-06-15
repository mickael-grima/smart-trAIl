package database

import (
    "fmt"
    "os"
)

type Environment struct {
    address  string
    username string
    password string
    dbname   string
}

func (env *Environment) dsn() string {
    return fmt.Sprintf(
        "%s:%s@tcp(%s)/%s?charset=utf8mb4&parseTime=True&loc=Local",
        env.username, env.password, env.address, env.dbname)
}

// loadEnv load environments from OS to Environment struct
func loadEnv() *Environment {
    return &Environment{
        address:  os.Getenv("MYSQL_ADDRESS"),
        username: os.Getenv("MYSQL_USERNAME"),
        password: os.Getenv("MYSQL_PASSWORD"),
        dbname:   os.Getenv("MYSQL_DBNAME"),
    }
}
