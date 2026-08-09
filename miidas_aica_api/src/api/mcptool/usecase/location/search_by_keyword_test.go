package location

import (
	"aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/public/master"
	"testing"

	"github.com/stretchr/testify/assert"
)

func Test_SearchByKeywordUseCase_Execute(t *testing.T) {
	expectedResultWhenExists := master.PrefectureCities{
		{
			PrefectureID:   master.PrefectureID(1),
			PrefectureName: "北海道",
			CityID:         master.CityID(11002),
			CityName:       "札幌市",
			Name:           "北海道札幌市",
			Kana:           "北海道さっぽろし",
		},
	}

	expectedResultWhenNotExists := master.PrefectureCities{}

	t.Run("キーワードを含む都道府県が存在する場合", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockCache.On("SearchLocation", "北海道").Return(expectedResultWhenExists).Once()

		actual := NewSearchByKeywordUseCase(mockCache, mockLogger).Execute("北海道")

		assert.Equal(t, expectedResultWhenExists, actual)
		mockCache.AssertExpectations(t)
	})

	t.Run("キーワードを含む都道府県が存在しない場合", func(t *testing.T) {
		mockLogger := new(mock.MockLogger)
		mockCache := new(mockCacheProvider)
		mockCache.On("SearchLocation", "存在しない都道府県").Return(expectedResultWhenNotExists).Once()

		actual := NewSearchByKeywordUseCase(mockCache, mockLogger).Execute("存在しない都道府県")

		assert.Equal(t, expectedResultWhenNotExists, actual)
		mockCache.AssertExpectations(t)
	})
}
