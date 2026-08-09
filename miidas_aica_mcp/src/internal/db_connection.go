package internal

import (
	"aica/mcp/sdk/env"
	"aica/mcp/sdk/gormio"
	"aica/mcp/sdk/logger"
	"aica/mcp/sdk/postgresql"
	"errors"
	"time"

	"gorm.io/gorm"
)

const (
	defaultDBName = "postgres"
	defaultPort   = 5432
)

var (
	postgresDB *gorm.DB
)

func SetupMCPDB(category string, debugMode bool, l logger.LevelLogger) error {
	prefixer := env.NewPrefixer(env.Prefix, category, "DB")

	host, err := prefixer.Get("HOST")
	if err != nil {
		return errors.New("DB HOST is not set")
	}

	port, err := prefixer.GetInt("PORT")
	if err != nil {
		l.Warn("DB PORT is not set. Use default port")
		port = defaultPort
	}

	user, err := prefixer.Get("USER")
	if err != nil {
		return errors.New("DB USER is not set")
	}

	password, err := prefixer.Get("PASSWORD")
	if err != nil {
		return errors.New("DB PASSWORD is not set")
	}

	dbName, err := prefixer.Get("NAME")
	if err != nil {
		l.Warn("DB NAME is not set. Use default name")
		dbName = defaultDBName
	}

	sslmode, _ := prefixer.Get("SSLMODE")

	conn, err := postgresql.NewConnection(user, password, host, port, dbName, sslmode, postgresql.ConnMaxLifetime(time.Duration(postgresql.StandardConnMaxLifetimeSec)*time.Second))
	if err != nil {
		return err
	}

	postgresDB, err = gormio.OpenPostgresSQL(conn, category, debugMode)
	if err != nil {
		return err
	}

	return err
}

func MCPDBConnection() *gorm.DB {
	return postgresDB
}
