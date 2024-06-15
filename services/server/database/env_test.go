package database

import (
    "testing"
)

func TestEnvironment_loadEnv(t *testing.T) {
    testCases := []struct{
        name        string
        address     string
        username    string
        password    string
        dbname      string
        expectedDSN string
    }{
        {
            name:        "no-port",
            address:     "localhost",
            username:    "root",
            password:    "xxx",
            dbname:      "test",
            expectedDSN: "root:xxx@tcp(localhost)/test?charset=utf8mb4&parseTime=True&loc=Local",
        },
        {
            name:        "with-port",
            address:     "localhost:3306",
            username:    "root",
            password:    "xxx",
            dbname:      "test",
            expectedDSN: "root:xxx@tcp(localhost:3306)/test?charset=utf8mb4&parseTime=True&loc=Local",
        },
    }

    for _, testCase := range testCases {
        t.Run(testCase.name, func(tt *testing.T) {
            tt.Setenv("MYSQL_ADDRESS", testCase.address)
            tt.Setenv("MYSQL_USERNAME", testCase.username)
            tt.Setenv("MYSQL_PASSWORD", testCase.password)
            tt.Setenv("MYSQL_DBNAME", testCase.dbname)

            env := loadEnv()
            dsn := env.dsn()
            if dsn != testCase.expectedDSN {
                tt.Fatalf("Expected %s as dsn, got %s instead", testCase.expectedDSN, dsn)
            }
        })
    }
}
