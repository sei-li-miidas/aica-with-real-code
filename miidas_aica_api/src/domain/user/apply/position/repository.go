package position

import (
	"errors"
	"time"

	"gorm.io/gorm"

	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/business"
	"aica/api/domain/user/apply/company"
)

// repository .
type (
	RPositionRepository struct {
		db *gorm.DB
	}
)

func NewReadPositionRepository(db *gorm.DB) *RPositionRepository {
	return &RPositionRepository{
		db: db,
	}
}

func (r *RPositionRepository) Get(id ID) (*Position, error) {
	return r.get(id)
}

func (r *RPositionRepository) get(id ID) (*Position, error) {
	var row Position

	q := r.db.Where("id = ?", id)
	if err := q.Take(&row).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &row, nil
}

func (r *RPositionRepository) GetByCompanyID(companyID company.ID) (Positions, error) {
	var rows Positions
	if err := r.db.Where("company_id = ?", companyID).
		Find(&rows).Error; err != nil {
		return nil, err
	}
	return rows, nil
}

func (r *RPositionRepository) GetByIDs(ids []ID) (Positions, error) {
	var rows Positions
	if err := r.db.Where("id IN (?)", ids).
		Find(&rows).Error; err != nil {
		return nil, err
	}
	return rows, nil
}

func (r *RPositionRepository) GetLatest(importedAt time.Time, sourceID int, chunkSize int) (Positions, error) {
	var positions Positions

	query := r.db.
		Where("(imported_at = ? AND id > ?) OR imported_at > ?", importedAt, sourceID, importedAt).
		Where("detail ->> '$.EmploymentType.ID' IN ?", []master.PositionEmploymentTypeID{
			master.PositionEmploymentTypeIDEmployee,
			master.PositionEmploymentTypeIDContract,
		}).
		Where("detail ->> '$.MainJobText' IS NOT NULL").
		Order("imported_at ASC, id ASC").
		Limit(chunkSize)

	if result := query.Find(&positions); result.Error != nil {
		return nil, result.Error
	}

	return positions, nil
}

func (r *RPositionRepository) GetCompanyID(id ID) (*company.ID, error) {
	var result struct {
		CompanyID company.ID `gorm:"column:company_id"`
	}

	if err := r.db.Model(&Position{}).Select("company_id").Where("id = ?", id).First(&result).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &result.CompanyID, nil
}

func (r *RPositionRepository) GetBusinessID(id ID) (*business.ID, error) {
	var result struct {
		BusinessID business.ID `gorm:"column:business_id"`
	}

	if err := r.db.Model(&Position{}).Select("JSON_EXTRACT(detail, '$.BusinessID') as business_id").Where("id = ?", id).First(&result).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, nil
		}
		return nil, err
	}
	return &result.BusinessID, nil
}
