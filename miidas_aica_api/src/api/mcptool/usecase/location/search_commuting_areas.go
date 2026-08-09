package location

import (
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	"aica/api/sdk/logger"
)

type searchCommutingAreaCacheProvider interface {
	PrefectureCities() master.PrefectureCities
}

// SearchCommutingAreasUseCase .
type SearchCommutingAreasUseCase struct {
	repository  *commutingAreaSearcher
	masterCache searchCommutingAreaCacheProvider
	logger      logger.LevelLogger
}

// NewSearchByAreaUseCase .
func NewSearchCommutingAreasUseCase(repository commutingAreaSearcher, masterCache searchCommutingAreaCacheProvider, l logger.LevelLogger) *SearchCommutingAreasUseCase {
	return &SearchCommutingAreasUseCase{
		repository:  &repository,
		masterCache: masterCache,
		logger:      l,
	}
}

// Execute 検索
func (uc *SearchCommutingAreasUseCase) Execute(req *shared.LocationRequest) master.PrefectureCities {
	cities := uc.masterCache.PrefectureCities().GetByName(req.PrefectureName, req.CityName)

	// 居住地の場合、通勤エリアを検索
	if len(cities) == 0 {
		uc.logger.Error("SearchCommutingAreasUseCase 居住地が見つかりませんでした。", "PrefectureName", req.PrefectureName, "CityName", req.CityName)
		return nil
	}
	// 居住地
	residence := cities[0]
	// リポジトリから通勤圏を検索
	prefectureCities, err := (*uc.repository).SearchCommutingAreas(int(residence.CityID))
	if err != nil {
		uc.logger.Error("SearchCommutingAreasUseCase 居住地からの通勤圏の検索に失敗しました。", "error", err)
		return nil
	}

	return prefectureCities
}
