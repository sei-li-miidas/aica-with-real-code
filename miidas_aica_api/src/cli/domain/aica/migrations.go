package aica

import (
	"time"

	"gorm.io/datatypes"
)

type (
	Migrations struct {
		ID             uint           `gorm:"primaryKey;autoIncrement:true"`
		Name           string         `gorm:"column:table_name"`
		LastImportedAt time.Time      `gorm:"column:last_imported_at"`
		LastSourceID   int            `gorm:"column:last_source_id"`
		Detail         datatypes.JSON `gorm:"column:detail"`
		FinishedAt     time.Time
	}
)

func (t Migrations) TableName() string {
	return "migrations"
}
