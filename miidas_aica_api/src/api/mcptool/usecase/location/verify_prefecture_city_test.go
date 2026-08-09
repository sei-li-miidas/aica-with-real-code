package location

import (
	"aica/api/api/mcptool/testutil/mock"
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	"testing"

	"github.com/stretchr/testify/assert"
)

func newDummyPrefectureCities() master.PrefectureCities {
	return master.PrefectureCities{
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(11002),
			CityName:       "札幌市",
		},
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(12025),
			CityName:       "函館市",
		},
	}
}

func Test_PrefectureCityUseCase_Execute(t *testing.T) {
	allDummyCities := newDummyPrefectureCities()

	t.Run("指定された都道府県・市区町村が存在する場合", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockCache.On("PrefectureCities").Return(allDummyCities).Once()

		actual := NewVerifyPrefectureCityUseCase(mockCache, mockLogger).Execute([]*shared.LocationRequest{
			{
				PrefectureName: "北海道",
				CityName:       "札幌",
			},
		})

		assert.Equal(t, master.PrefectureCities{
			{
				PrefectureID:   master.PrefectureID(1),
				PrefectureName: "北海道",
				CityID:         master.CityID(11002),
				CityName:       "札幌市",
			},
		}, actual)
		mockCache.AssertExpectations(t)
	})

	t.Run("指定された都道府県・市区町村が存在しない場合", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockCache.On("PrefectureCities").Return(allDummyCities).Once()

		actual := NewVerifyPrefectureCityUseCase(mockCache, mockLogger).Execute([]*shared.LocationRequest{
			{
				PrefectureName: "存在しない都道府県",
				CityName:       "存在しない市区町村",
			},
		})

		assert.Equal(t, master.PrefectureCities{}, actual)
		mockCache.AssertExpectations(t)
	})

	t.Run("複数の都道府県・市区町村をまとめて検証できる", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockCache.On("PrefectureCities").Return(allDummyCities).Once()

		actual := NewVerifyPrefectureCityUseCase(mockCache, mockLogger).Execute([]*shared.LocationRequest{
			{
				PrefectureName: "北海道",
				CityName:       "札幌",
			},
			{
				PrefectureName: "北海道",
				CityName:       "函館",
			},
			{
				PrefectureName: "北海道",
				CityName:       "札幌",
			},
		})

		assert.Equal(t, master.PrefectureCities{
			{
				PrefectureID:   master.PrefectureID(1),
				PrefectureName: "北海道",
				CityID:         master.CityID(11002),
				CityName:       "札幌市",
			},
			{
				PrefectureID:   master.PrefectureID(1),
				PrefectureName: "北海道",
				CityID:         master.CityID(12025),
				CityName:       "函館市",
			},
		}, actual)
		mockCache.AssertExpectations(t)
	})
}
