package commutingarea

import (
	"aica/api/domain/public/master"

	"gorm.io/gorm"
)

type (
	CommutingAreaRepository struct {
		db *gorm.DB
	}
)

// NewCommutingAreaRepository
func NewCommutingAreaRepository(db *gorm.DB) *CommutingAreaRepository {
	return &CommutingAreaRepository{
		db: db,
	}
}

// ある市区町村IDから通勤圏を検索する
func (r *CommutingAreaRepository) SearchCommutingAreas(originCityID int) ([]*master.PrefectureCity, error) {
	var commutingAreas []*CommutingArea
	result := r.db.Model(CommutingArea{}).
		Where("origin_id = ?", originCityID).
		Where("deleted_at IS NULL").
		Order("rank ASC").
		Find(&commutingAreas)
	if result.Error != nil {
		return nil, result.Error
	}

	var prefectureCities []*master.PrefectureCity

	for _, cm := range commutingAreas {
		pc := master.PrefectureCity{
			CityID:         master.CityID(cm.DestinationId),
			CityName:       master.CityName(cm.DestinationName),
			PrefectureID:   master.PrefectureID(cm.DestinationPrefectureId),
			PrefectureName: cm.DestinationPrefectureName,
		}
		prefectureCities = append(prefectureCities, &pc)
	}

	return prefectureCities, nil
}
