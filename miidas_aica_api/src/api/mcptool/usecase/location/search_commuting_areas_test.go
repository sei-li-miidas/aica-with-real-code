package location

import (
	"aica/api/api/mcptool/testutil/mock"
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
)

const hiroshima_city_id = 341002

func setupTestData() (master.PrefectureCities, map[master.CityID][]master.CityID) {
	prefectureCitiesData := master.PrefectureCities{
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(11002),
			CityName:       "札幌市",
		},
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(12033),
			CityName:       "小樽市",
		},
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(12041),
			CityName:       "旭川市",
		},
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(12025),
			CityName:       "函館市",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(hiroshima_city_id),
			CityName:       "広島市",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(343021),
			CityName:       "府中町",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(342131),
			CityName:       "廿日市市",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(342122),
			CityName:       "東広島市",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(343048),
			CityName:       "海田町",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(342025),
			CityName:       "呉市",
		},
		{
			PrefectureID:   master.PrefectureID(34),
			PrefectureName: "広島県",
			CityID:         master.CityID(343099),
			CityName:       "坂町",
		},
	}

	cityCommutingAreaData := map[master.CityID][]master.CityID{
		master.CityID(341002): {
			master.CityID(341002),
			master.CityID(343021),
			master.CityID(342131),
			master.CityID(342122),
			master.CityID(343048),
			master.CityID(342025),
			master.CityID(343099),
		},
	}

	return prefectureCitiesData, cityCommutingAreaData
}

func TestSearchCommutingAreasUseCase_AdditionalBranches(t *testing.T) {
	prefectureCitiesData, _ := setupTestData()

	t.Run("居住地が見つからない場合、nilを返す", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockRepo := new(mockCommutingAreaRepository)
		mockCache.On("PrefectureCities").Return(prefectureCitiesData)

		uc := NewSearchCommutingAreasUseCase(mockRepo, mockCache, mockLogger)
		res := uc.Execute(&shared.LocationRequest{
			LocationType:   shared.LOCATION_TYPE_RESIDENCE,
			PrefectureName: "東京都",
			CityName:       "存在しない市",
		})
		assert.Nil(t, res)
		mockCache.AssertExpectations(t)
	})

	t.Run("居住地の通勤圏検索でリポジトリエラー時にnilを返す", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockRepo := new(mockCommutingAreaRepository)
		mockCache.On("PrefectureCities").Return(prefectureCitiesData)
		mockRepo.On("SearchCommutingAreas", 11002).Return([]*master.PrefectureCity(nil), errors.New("repo failed")).Once()

		uc := NewSearchCommutingAreasUseCase(mockRepo, mockCache, mockLogger)
		res := uc.Execute(&shared.LocationRequest{
			LocationType:   shared.LOCATION_TYPE_RESIDENCE,
			PrefectureName: "北海道",
			CityName:       "札幌市",
		})
		assert.Nil(t, res)
		mockCache.AssertExpectations(t)
		mockRepo.AssertExpectations(t)
	})
}

func Test_SearchCommutingAreasUseCase_Execute(t *testing.T) {
	prefectureCitiesData, _ := setupTestData()

	tests := []struct {
		name      string
		req       *shared.LocationRequest
		setup     func(m *mockCacheProvider)
		setupRepo func(m *mockCommutingAreaRepository)
		expected  master.PrefectureCities
	}{
		{
			name: "フルリモートの場合、nilを返す",
			req: &shared.LocationRequest{
				LocationType: shared.LOCATION_TYPE_FULL_REMOTE_WORK,
			},
			setup: func(m *mockCacheProvider) {
				m.On("PrefectureCities").Return(master.PrefectureCities{})
			},
			setupRepo: func(m *mockCommutingAreaRepository) {},
			expected:  nil,
		},
		{
			name: "希望勤務地の場合、指定された都市を返す",
			req: &shared.LocationRequest{
				LocationType:   shared.LOCATION_TYPE_WORK_LOCATION,
				PrefectureName: "北海道",
				CityName:       "札幌市",
			},
			setup: func(m *mockCacheProvider) {
				m.On("PrefectureCities").Return(prefectureCitiesData)
			},
			setupRepo: func(m *mockCommutingAreaRepository) {
				sapporoResult := []*master.PrefectureCity{
					{
						PrefectureID:   master.PrefectureID(1),
						PrefectureName: "北海道",
						CityID:         master.CityID(11002),
						CityName:       "札幌市",
					},
				}
				m.On("SearchCommutingAreas", 11002).Return(sapporoResult, nil).Once()
			},
			expected: master.PrefectureCities{
				{
					PrefectureID:   master.PrefectureID(1),
					PrefectureName: "北海道",
					CityID:         master.CityID(11002),
					CityName:       "札幌市",
				},
			},
		},
		{
			name: "居住地の場合、通勤可能な都市全てを返す",
			req: &shared.LocationRequest{
				LocationType:   shared.LOCATION_TYPE_RESIDENCE,
				PrefectureName: "広島県",
				CityName:       "広島市",
			},
			setup: func(m *mockCacheProvider) {
				m.On("PrefectureCities").Return(prefectureCitiesData)
			},
			setupRepo: func(m *mockCommutingAreaRepository) {
				hiroshimaResult, hiroshimaError := mockSearchCommutingAreas(hiroshima_city_id)
				m.On("SearchCommutingAreas", hiroshima_city_id).
					Return(hiroshimaResult, hiroshimaError).
					Once()
			},
			expected: master.PrefectureCities{
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(341002),
					CityName:       "広島市",
				},
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(343021),
					CityName:       "府中町",
				},
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(342131),
					CityName:       "廿日市市",
				},
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(342122),
					CityName:       "東広島市",
				},
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(343048),
					CityName:       "海田町",
				},
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(342025),
					CityName:       "呉市",
				},
				{
					PrefectureID:   master.PrefectureID(34),
					PrefectureName: "広島県",
					CityID:         master.CityID(343099),
					CityName:       "坂町",
				},
			},
		},
		{
			name: "LocationTypeが不明な場合、nilを返す",
			req: &shared.LocationRequest{
				LocationType:   "不明な種別",
				PrefectureName: "存在しない都道府県",
				CityName:       "存在しない市区町村",
			},
			setup: func(m *mockCacheProvider) {
				m.On("PrefectureCities").Return(prefectureCitiesData)
			},
			setupRepo: func(m *mockCommutingAreaRepository) {},
			expected:  nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			mockLogger := new(mock.MockLogger)
			mockCache := new(mockCacheProvider)
			mockRepo := new(mockCommutingAreaRepository)

			tt.setup(mockCache)
			tt.setupRepo(mockRepo)

			actual := NewSearchCommutingAreasUseCase(mockRepo, mockCache, mockLogger).Execute(tt.req)
			assert.Equal(t, tt.expected, actual)
			mockCache.AssertExpectations(t)
			mockRepo.AssertExpectations(t)
		})
	}
}
