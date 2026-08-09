package location

import (
	"aica/api/domain/public/master"
	"aica/api/sdk/logger"
)

type searchLocationCacheProvider interface {
	SearchLocation(keyword string) master.PrefectureCities
}

type (
	// SearchByKeywordUseCase .
	SearchByKeywordUseCase struct {
		masterCache searchLocationCacheProvider
		logger      logger.LevelLogger
	}
)

// NewSearchByAreaUseCase .
func NewSearchByKeywordUseCase(masterCache searchLocationCacheProvider, l logger.LevelLogger) *SearchByKeywordUseCase {
	return &SearchByKeywordUseCase{
		masterCache: masterCache,
		logger:      l,
	}
}

// Execute 検索
func (uc *SearchByKeywordUseCase) Execute(keyword string) master.PrefectureCities {
	return uc.masterCache.SearchLocation(keyword)
}
