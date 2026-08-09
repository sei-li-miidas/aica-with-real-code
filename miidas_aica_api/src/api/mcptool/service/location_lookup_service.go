package service

import (
	"fmt"

	"aica/api/domain/public/master"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"aica/api/sdk/util"
)

type commutingAreaSearcher interface {
	SearchCommutingAreas(originCityID int) ([]*master.PrefectureCity, error)
}

type LocationLookupService struct {
	logger                logger.LevelLogger
	cache                 *master.CacheProvider
	commutingAreaSearcher commutingAreaSearcher
}

func NewLocationLookupService(
	logger logger.LevelLogger,
	cache *master.CacheProvider,
	commutingAreaSearcher commutingAreaSearcher,
) *LocationLookupService {
	return &LocationLookupService{
		logger:                logger,
		cache:                 cache,
		commutingAreaSearcher: commutingAreaSearcher,
	}
}

// 居住地からの通勤可能の市区町村IDを返す
func (s *LocationLookupService) GetCommutingAreasFromResidence(prefectureName string, cityName string) ([]int, error) {
	originalPrefectureName, originalCityName := prefectureName, cityName
	// 東京23区のいずれかであれば、「東京23区」に変換する
	prefectureName, cityName = util.MaybeReplaceTokyoWardName(prefectureName, cityName)
	// 居住地を検索して市区町村と都道府県IDを取得
	cities := s.cache.PrefectureCities().GetByName(prefectureName, cityName)
	if len(cities) == 0 {
		return nil, merr.ErrInvalidRequest.WithCause(
			fmt.Errorf(
				"居住地の市区町村が見つかりませんでした（都道府県: %s, 市区町村: %s）。正しい市区町村名を指定してください。",
				originalPrefectureName,
				originalCityName,
			),
		)
	}

	residenceCityID := int(cities[0].CityID)
	prefectureCities, err := s.commutingAreaSearcher.SearchCommutingAreas(residenceCityID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(err)
	}

	results := make([]int, 0, len(prefectureCities)+1)
	for _, prefectureCity := range prefectureCities {
		results = append(results, int(prefectureCity.CityID))
	}

	// 通勤圏の市区町村には居住市区町村が含まれない。
	// 居住地からポジション検索を行う際には居住市区町村も含むため、通勤圏に居住地を追加する。
	results = append(results, residenceCityID)

	return results, nil
}

// 希望勤務地の都道府県名と市区町村名から市区町村IDを返す
func (s *LocationLookupService) GetCityIDsFromWorkLocations(locations []struct{ PrefectureName, CityName string }) ([]int, error) {
	if len(locations) == 0 {
		return []int{}, nil
	}

	cityIDs := make([]int, 0, len(locations))
	for _, loc := range locations {
		// 東京23区のいずれかであれば、「東京23区」に変換する
		prefectureName, cityName := util.MaybeReplaceTokyoWardName(loc.PrefectureName, loc.CityName)
		cities := s.cache.PrefectureCities().GetByName(prefectureName, cityName)
		if len(cities) == 0 {
			return nil, merr.ErrInvalidRequest.WithCause(
				fmt.Errorf(
					"希望勤務地の市区町村が見つかりませんでした（都道府県: %s, 市区町村: %s）。正しい市区町村名を指定してください。",
					loc.PrefectureName,
					loc.CityName,
				),
			)
		}
		cityIDs = append(cityIDs, int(cities[0].CityID))
	}

	return cityIDs, nil
}
