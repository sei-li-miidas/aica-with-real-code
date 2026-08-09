package gormio

import (
	"aica/api/sdk/env"
	"aica/api/sdk/mysql"
	"aica/api/sdk/postgresql"
	"time"

	"gorm.io/gorm"
)

func OpenAgentDB(serviceName string, category string, debugMode bool) (*gorm.DB, error) {
	p := env.NewPrefixer(env.Prefix, serviceName, "DB")

	host := p.MustGet("HOST")

	port, err := p.GetInt("PORT")
	if err != nil {
		port = 5432
	}

	user := p.MustGet("USER")

	pass := p.MustGet("PASSWORD")

	dbName, err := p.Get("NAME")
	if err != nil {
		dbName = "postgres"
	}

	sslmode, err := p.Get("SSLMODE")
	if err != nil {
		sslmode = ""
	}

	conn, err := postgresql.NewConnection(user, pass, host, port, dbName, sslmode, postgresql.ConnMaxLifetime(time.Duration(postgresql.StandardConnMaxLifetimeSec)*time.Second))
	if err != nil {
		return nil, err
	}

	return OpenPostgresSQL(conn, category, debugMode)
}

func OpenMiidasDBReader(serviceName string, category string, debugMode bool) (*gorm.DB, error) {
	p := env.NewPrefixer(env.Prefix, serviceName, "MIIDAS", "DB")

	host := p.MustGet("HOST")

	port, err := p.GetInt("PORT")
	if err != nil {
		port = 3306
	}

	user := p.MustGet("USER")

	pass := p.MustGet("PASSWORD")

	mCfg := mysql.NewConfig(user, pass, host, port)
	conn, err := mysql.NewConnection(mCfg, mysql.ConnMaxLifetime(time.Duration(mysql.StandardConnMaxLifetimeSec)*time.Second))
	if err != nil {
		return nil, err
	}

	return Open(conn, category, debugMode)
}
