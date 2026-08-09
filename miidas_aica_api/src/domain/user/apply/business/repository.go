package business

import (
	"errors"
	"time"

	"gorm.io/gorm"

	"aica/api/domain/user/apply/company"
)

type (
	RBusinessRepository struct {
		db *gorm.DB
	}
)

func NewReadBusinessRepository(db *gorm.DB) *RBusinessRepository {
	return &RBusinessRepository{
		db: db,
	}
}

func (r *RBusinessRepository) Get(id ID) (*Business, error) {
	var row business
	if err := r.db.Where("id = ?", id).Take(&row).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	b := Business{
		ID:             ID(row.ID),
		CompanyID:      company.ID(row.CompanyID),
		Detail:         row.Detail,
		TrashedAt:      row.TrashedAt,
		LastModifiedAt: row.LastModifiedAt,
		ImportedAt:     row.ImportedAt,
	}
	return &b, nil
}

func (r *RBusinessRepository) GetByCompanyID(companyID company.ID) ([]Business, error) {
	var row []business
	if err := r.db.Where("company_id = ?", companyID).Find(&row).Error; err != nil {
		return nil, err
	}
	ret := make([]Business, 0, len(row))
	for idx := range row {
		ret = append(ret, Business{
			ID:             ID(row[idx].ID),
			CompanyID:      company.ID(row[idx].CompanyID),
			Detail:         row[idx].Detail,
			TrashedAt:      row[idx].TrashedAt,
			LastModifiedAt: row[idx].LastModifiedAt,
			ImportedAt:     row[idx].ImportedAt,
		})
	}
	return ret, nil
}

func (r *RBusinessRepository) GetByIDs(ids []ID) ([]Business, error) {
	var rows []business
	if err := r.db.Where("id IN (?)", ids).
		Find(&rows).Error; err != nil {
		return nil, err
	}

	bs := make([]Business, 0, len(rows))
	for i := range rows {
		row := rows[i]
		b := Business{
			ID:             ID(row.ID),
			CompanyID:      company.ID(row.CompanyID),
			Detail:         row.Detail,
			TrashedAt:      row.TrashedAt,
			LastModifiedAt: row.LastModifiedAt,
			ImportedAt:     row.ImportedAt,
		}
		bs = append(bs, b)
	}
	return bs, nil
}

type business struct {
	ID             int `gorm:"primaryKey;autoIncrement:false"`
	CompanyID      int
	Detail         Detail
	TrashedAt      *time.Time
	LastModifiedAt time.Time
	ImportedAt     time.Time
}

func (business) TableName() string {
	return "user_apply.business"
}
