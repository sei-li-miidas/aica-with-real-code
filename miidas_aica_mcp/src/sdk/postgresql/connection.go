package postgresql

import (
	"database/sql"
	"fmt"
	"time"

	_ "github.com/lib/pq"
)

type (
	// ConnOption コネクションのオプション設定
	ConnOption func(db *sql.DB)
)

const (
	// StandardConnMaxLifetimeSec ConnMaxLifetimeの秒数
	StandardConnMaxLifetimeSec = 10 // FIXME
)

func NewConnection(user, password, hostname string, port int, dbName string, sslmode string, connOpts ...ConnOption) (*sql.DB, error) {
	dbParam := fmt.Sprintf("postgres://%v:%v@%v:%v/%v", user, password, hostname, port, dbName)
	if sslmode != "" {
		dbParam += "?sslmode=" + sslmode
	}

	db, err := sql.Open("postgres", dbParam)
	if err != nil {
		return nil, err
	}
	for _, o := range connOpts {
		o(db)
	}
	return db, nil
}

// ConnMaxLifetime ConnMaxLifetimeを設定します。
func ConnMaxLifetime(lifetime time.Duration) func(*sql.DB) {
	return func(db *sql.DB) {
		db.SetConnMaxLifetime(lifetime)
	}
}
