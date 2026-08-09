package position

import (
	miidasPosition "aica/api/domain/user/apply/position"

	"gorm.io/gorm"
)

type (
	PositionRepository struct {
		db *gorm.DB
	}

	PositionSearchResult struct {
		ID       miidasPosition.ID
		Distance float64
	}
)

// NewPositionRepository .
func NewPositionRepository(db *gorm.DB) *PositionRepository {
	return &PositionRepository{
		db: db,
	}
}

func (r *PositionRepository) SemanticSearch(embedding string, distance float64, addConditions func(*gorm.DB) *gorm.DB) ([]*PositionSearchResult, error) {
	var positions []*PositionSearchResult

	query := r.db.Model(PositionVector{}).Select("position_id AS id, embedding <=> ? as distance", embedding).Where("embedding <=> ? <= ?", embedding, distance)
	if addConditions != nil {
		query = addConditions(query)
	}
	result := query.Order("distance").Find(&positions)

	if result.Error != nil {
		return nil, result.Error
	}

	return positions, nil
}

func (r *PositionRepository) Create(positionVectors []*PositionVector) error {
	return r.db.Create(positionVectors).Error
}

func (r *PositionRepository) Delete(positionID []miidasPosition.ID) error {
	return r.db.Where("position_id IN ?", positionID).Delete(&PositionVector{}).Error
}
