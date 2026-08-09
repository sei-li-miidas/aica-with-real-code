package aica

import (
	"errors"
	"fmt"
	"time"

	"gorm.io/gorm"
)

type MigrationsRepository struct {
	db *gorm.DB
}

func NewMigrationsRepository(db *gorm.DB) *MigrationsRepository {
	return &MigrationsRepository{db: db}
}

func (r *MigrationsRepository) GetLastImportedAtAndSourceID(tableName string) (*time.Time, *int, error) {
	if tableName == "" {
		return nil, nil, errors.New("table name cannot be empty")
	}

	var migration Migrations
	query := r.db.
		Where("table_name = ?", tableName).
		Order("finished_at DESC").
		Select("last_imported_at, last_source_id").
		Limit(1)

	if err := query.First(&migration).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil, nil
		}
		return nil, nil, fmt.Errorf("failed to fetch last successful execute date: %w", err)
	}

	return &migration.LastImportedAt, &migration.LastSourceID, nil
}

func (r *MigrationsRepository) Save(migration *Migrations) error {
	return r.db.Save(migration).Error
}
