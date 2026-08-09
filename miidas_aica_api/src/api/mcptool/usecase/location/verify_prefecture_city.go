package location

import (
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	"aica/api/sdk/logger"

	"github.com/samber/lo"
)

type prefectureCitiesCacheProvider interface {
	PrefectureCities() master.PrefectureCities
}

type (
	// VerifyPrefectureCityUseCase .
	VerifyPrefectureCityUseCase struct {
		masterCache prefectureCitiesCacheProvider
		logger      logger.LevelLogger
	}
)

// NewSearchByAreaUseCase .
func NewVerifyPrefectureCityUseCase(masterCache prefectureCitiesCacheProvider, l logger.LevelLogger) *VerifyPrefectureCityUseCase {
	return &VerifyPrefectureCityUseCase{
		masterCache: masterCache,
		logger:      l,
	}
}

// Execute 検索
func (uc *VerifyPrefectureCityUseCase) Execute(reqs []*shared.LocationRequest) master.PrefectureCities {
	allCities := uc.masterCache.PrefectureCities()
	cities := make(master.PrefectureCities, 0)
	for _, req := range reqs {
		cities = append(cities, allCities.GetByName(req.PrefectureName, req.CityName)...)
	}

	return lo.UniqBy(cities, func(city *master.PrefectureCity) master.CityID {
		return city.CityID
	})
}
