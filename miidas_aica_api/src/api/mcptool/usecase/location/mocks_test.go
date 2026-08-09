package location

import (
	"aica/api/domain/public/master"
	"fmt"

	"github.com/stretchr/testify/mock"
)

// mockCacheProvider CacheProviderのモック
type mockCacheProvider struct {
	mock.Mock
}

func (m *mockCacheProvider) SearchLocation(keyword string) master.PrefectureCities {
	args := m.Called(keyword)
	return args.Get(0).(master.PrefectureCities)
}

func (m *mockCacheProvider) PrefectureCities() master.PrefectureCities {
	args := m.Called()
	return args.Get(0).(master.PrefectureCities)
}

// リポジトリのモック
type mockCommutingAreaRepository struct {
	mock.Mock
}

func (repo *mockCommutingAreaRepository) SearchCommutingAreas(originCityID int) ([]*master.PrefectureCity, error) {
	args := repo.Called(originCityID)
	return args.Get(0).([]*master.PrefectureCity), args.Error(1)
}

// モック通勤圏検索関数
func mockSearchCommutingAreas(originCityID int) ([]*master.PrefectureCity, error) {
	prefectureCities, commutingAreas := setupTestData()
	cm, found := commutingAreas[master.CityID(originCityID)]
	if !found {
		return nil, fmt.Errorf("CommutingAreas NOT FOUND for originCityID %d\n", originCityID)
	}

	var result []*master.PrefectureCity
	for _, cityID := range cm {
		for _, pc := range prefectureCities {
			if pc.CityID != cityID {
				continue
			}
			result = append(result, pc)
			break
		}
	}

	return result, nil
}
