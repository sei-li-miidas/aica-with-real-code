package service

import (
	"errors"
	"testing"

	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/public/master"

	"github.com/stretchr/testify/assert"
)

type locationLookupRepoStub struct {
	results []*master.PrefectureCity
	err     error
}

func (s *locationLookupRepoStub) SearchCommutingAreas(_ int) ([]*master.PrefectureCity, error) {
	if s.err != nil {
		return nil, s.err
	}
	return s.results, nil
}

func TestLocationLookupService_GetCommutingAreasFromResidence(t *testing.T) {
	cp := master.NewCacheProviderWithCache(&master.Cache{
		PrefectureCities: master.PrefectureCities{
			{PrefectureName: "大阪府", CityName: "大阪市", CityID: 10001},
		},
	})

	svc := NewLocationLookupService(&tmock.MockLogger{}, cp, &locationLookupRepoStub{
		results: []*master.PrefectureCity{
			{CityID: 10002},
			{CityID: 10003},
		},
	})

	got, err := svc.GetCommutingAreasFromResidence("大阪府", "大阪市")
	assert.NoError(t, err)
	assert.Equal(t, []int{10002, 10003, 10001}, got)
}

func TestLocationLookupService_GetCommutingAreasFromResidence_ErrorCases(t *testing.T) {
	t.Run("居住地が見つからない場合", func(t *testing.T) {
		cp := master.NewCacheProviderWithCache(&master.Cache{
			PrefectureCities: master.PrefectureCities{},
		})
		svc := NewLocationLookupService(&tmock.MockLogger{}, cp, &locationLookupRepoStub{})

		got, err := svc.GetCommutingAreasFromResidence("大阪府", "不存在市")
		assert.Nil(t, got)
		assert.Error(t, err)
	})

	t.Run("リポジトリがエラーを返す場合", func(t *testing.T) {
		cp := master.NewCacheProviderWithCache(&master.Cache{
			PrefectureCities: master.PrefectureCities{
				{PrefectureName: "大阪府", CityName: "大阪市", CityID: 10001},
			},
		})
		svc := NewLocationLookupService(&tmock.MockLogger{}, cp, &locationLookupRepoStub{
			err: errors.New("db failed"),
		})

		got, err := svc.GetCommutingAreasFromResidence("大阪府", "大阪市")
		assert.Nil(t, got)
		assert.Error(t, err)
	})
}

func TestLocationLookupService_GetCityIDsFromWorkLocations(t *testing.T) {
	cp := master.NewCacheProviderWithCache(&master.Cache{
		PrefectureCities: master.PrefectureCities{
			{PrefectureName: "大阪府", CityName: "大阪市", CityID: 10001},
			{PrefectureName: "大阪府", CityName: "堺市", CityID: 10003},
		},
	})
	svc := NewLocationLookupService(&tmock.MockLogger{}, cp, &locationLookupRepoStub{})

	t.Run("正常に処理できる", func(t *testing.T) {
		got, err := svc.GetCityIDsFromWorkLocations([]struct{ PrefectureName, CityName string }{
			{PrefectureName: "大阪府", CityName: "大阪市"},
			{PrefectureName: "大阪府", CityName: "堺市"},
		})
		assert.NoError(t, err)
		assert.Equal(t, []int{10001, 10003}, got)
	})

	t.Run("データが見つからない場合", func(t *testing.T) {
		got, err := svc.GetCityIDsFromWorkLocations([]struct{ PrefectureName, CityName string }{
			{PrefectureName: "不存在県", CityName: "不存在市"},
		})
		assert.Nil(t, got)
		assert.Error(t, err)
	})
}
