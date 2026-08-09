package mysql

import (
	"database/sql"
	"time"

	"github.com/go-sql-driver/mysql"
)

type (
	// ConnOption コネクションのオプション設定
	ConnOption func(db *sql.DB)
)

const (
	// StandardConnMaxLifetimeSec ConnMaxLifetimeの秒数
	StandardConnMaxLifetimeSec = 10
	StandardMaxIdleConns       = 10
)

func NewConnection(cfg *mysql.Config, connOpts ...ConnOption) (*sql.DB, error) {
	db, err := sql.Open("mysql", cfg.FormatDSN())
	if err != nil {
		return nil, err
	}
	opts := []ConnOption{
		StdConnMaxLifetimeOpts,
		StdMaxIdleConnsOpts,
	}
	for _, o := range append(opts, connOpts...) {
		o(db)
	}
	return db, nil
}

// StdConnMaxLifetimeOpts 標準的な ConnMaxLifetimeを設定します。
func StdConnMaxLifetimeOpts(db *sql.DB) {
	ConnMaxLifetime(time.Duration(StandardConnMaxLifetimeSec) * time.Second)(db)
}

// StdMaxIdleConnsOpts 標準的な MaxIdleConnsを設定します。
func StdMaxIdleConnsOpts(db *sql.DB) {
	MaxIdleConns(StandardMaxIdleConns)(db)
}

// ConnMaxLifetime 任意のConnMaxLifetimeを設定します。
func ConnMaxLifetime(lifetime time.Duration) func(*sql.DB) {
	return func(db *sql.DB) {
		db.SetConnMaxLifetime(lifetime)
	}
}

// MaxIdleConns 任意のMaxIdleConnsを設定します。
func MaxIdleConns(idleConns int) func(*sql.DB) {
	return func(db *sql.DB) {
		db.SetMaxIdleConns(idleConns)
	}
}
