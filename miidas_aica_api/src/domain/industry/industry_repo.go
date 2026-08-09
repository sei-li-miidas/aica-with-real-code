package industry

import (
	"gorm.io/gorm"
)

type (
	IndustrySmallRepository struct {
		db *gorm.DB
	}

	IndustrySearchResult struct {
		ID          int
		Name        string
		Description string
		Distance    float64
	}
)

// NewIndustrySmallRepository .
func NewIndustrySmallRepository(db *gorm.DB) *IndustrySmallRepository {
	return &IndustrySmallRepository{
		db: db,
	}
}

func (r *IndustrySmallRepository) SemanticSearch(embedding string, distance float64, addConditions func(*gorm.DB) *gorm.DB) ([]*IndustrySearchResult, error) {
	query := r.db.Model(IndustrySmallVector{}).Select("id, name, description, embedding <=> ? as distance", embedding).Joins("JOIN industry_small ON industry_small.id = industry_small_vector.industry_small_id").Where("embedding <=> ? <= ?", embedding, distance).Order("distance")
	if addConditions != nil {
		query = addConditions(query)
	}

	var industries []*IndustrySearchResult
	result := query.Find(&industries)
	if result.Error != nil {
		return nil, result.Error
	}

	return industries, nil
}

func (r *IndustrySmallRepository) All() ([]*IndustrySmall, error) {
	var industries []*IndustrySmall
	result := r.db.Find(&industries)
	if result.Error != nil {
		return nil, result.Error
	}

	return industries, nil
}

func (r *IndustrySmallRepository) DeleteByIds(ids []int) error {
	return r.db.Delete(&IndustrySmallVector{}, ids).Error
}

func (r *IndustrySmallRepository) DeleteAll() error {
	return r.db.Where("1 = 1").Delete(&IndustrySmallVector{}).Error
}
