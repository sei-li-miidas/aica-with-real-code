package position

import (
	"testing"

	"github.com/stretchr/testify/assert"

	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
)

type countingLocationLookupStub struct {
	commutingResult []int
	commutingCalls  int
	workCalls       int
	err             error
}

func (s *countingLocationLookupStub) GetCommutingAreasFromResidence(_ string, _ string) ([]int, error) {
	s.commutingCalls++
	if s.err != nil {
		return nil, s.err
	}
	return s.commutingResult, nil
}

func (s *countingLocationLookupStub) GetCityIDsFromWorkLocations(locations []struct{ PrefectureName, CityName string }) ([]int, error) {
	s.workCalls++
	if s.err != nil {
		return nil, s.err
	}
	if len(locations) == 0 {
		return nil, nil
	}
	switch locations[0].CityName {
	case "堺市":
		return []int{10003}, nil
	case "豊中市":
		return []int{10005}, nil
	default:
		return nil, nil
	}
}

func TestJobSpecificResolver_Impl_Branches(t *testing.T) {
	cache := &master.Cache{
		JobTypeSmalls: master.JobTypeSmalls{
			&master.JobTypeSmall{ID: 10001, Name: "エンジニア"},
		},
		Skills: master.Skills{
			&master.Skill{ID: 1, Name: "言語（all）$Go"},
		},
		PrefectureCities: master.PrefectureCities{
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("大阪市"), CityID: 10001},
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("堺市"), CityID: 10003},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{Value: 1, Name: "あり", UserSideName: "あり"},
				{Value: 2, Name: "なし", UserSideName: "なし"},
			},
		},
	}

	locationLookup := newLocationLookupServiceWithCache(cache, map[int][]*master.PrefectureCity{
		10001: {},
	})
	resolver := NewJobSpecificSearchResolver(newCacheServiceWithCache(cache), locationLookup)

	t.Run("職種小分類IDを解決できる", func(t *testing.T) {
		ids, err := resolver.ResolveJobTypeSmallIDs([]string{"エンジニア"})
		assert.NoError(t, err)
		assert.Equal(t, []int32{10001}, ids)
	})

	t.Run("居住地と勤務地の両方を解決できる", func(t *testing.T) {
		cityIDs, residence, commutingAreas, workLocations, err := resolver.ResolveLocations([]*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "大阪府", CityName: "大阪市"},
			{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "大阪府", CityName: "堺市"},
		}, false)
		assert.NoError(t, err)
		assert.NotNil(t, residence)
		assert.Empty(t, commutingAreas)
		assert.Len(t, workLocations, 1)
		assert.ElementsMatch(t, []int32{10001, 10003}, cityIDs)
	})

	t.Run("フルリモート可能な場合に勤務地を解決できる", func(t *testing.T) {
		cityIDs, _, commutingAreas, workLocations, err := resolver.ResolveLocations([]*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "大阪府", CityName: "大阪市"},
		}, true)
		assert.NoError(t, err)
		assert.Nil(t, cityIDs)
		assert.Empty(t, commutingAreas)
		assert.Empty(t, workLocations)
	})

	t.Run("スキルを解決できる", func(t *testing.T) {
		skills, err := resolver.ResolveSkills([]string{"Go"})
		assert.NoError(t, err)
		assert.Len(t, skills, 1)
	})

	t.Run("休日と残業時間が不正な場合", func(t *testing.T) {
		_, err := resolver.ResolveDayOffs(&[]string{"invalid"})
		assert.Error(t, err)
		_, err = resolver.ResolveAverageOvertime(loPtr("invalid"))
		assert.Error(t, err)
	})

	t.Run("営業スタイルを解決できる", func(t *testing.T) {
		v, err := resolver.ResolveSalesStyleDive(loPtr("あり"))
		assert.NoError(t, err)
		assert.Equal(t, int32(1), v)
		_, err = resolver.ResolveSalesStyleDive(loPtr("invalid"))
		assert.Error(t, err)
	})
}

func TestJobSpecificResolver_RemainingBranches(t *testing.T) {
	cache := &master.Cache{
		PrefectureCities: master.PrefectureCities{
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("大阪市"), CityID: 10001},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{Value: 1, Name: "あり", UserSideName: "あり"},
			},
		},
	}
	resolver := NewJobSpecificSearchResolver(
		newCacheServiceWithCache(cache),
		newLocationLookupServiceWithCache(cache, map[int][]*master.PrefectureCity{
			10001: {},
		}),
	)

	dayOffs, err := resolver.ResolveDayOffs(nil)
	assert.NoError(t, err)
	assert.Nil(t, dayOffs)

	overtime, err := resolver.ResolveAverageOvertime(nil)
	assert.NoError(t, err)
	assert.Equal(t, int32(0), overtime)

	sales, err := resolver.ResolveSalesStyleDive(nil)
	assert.NoError(t, err)
	assert.Equal(t, int32(0), sales)

	_, _, _, _, err = resolver.ResolveLocations([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "存在しない都道府県", CityName: "存在しない市"},
	}, false)
	assert.Error(t, err)

	cityIDs, residence, commutingAreas, workLocations, err := resolver.ResolveLocations([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "大阪府", CityName: "大阪市"},
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "大阪府", CityName: "大阪市"},
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "大阪府", CityName: "大阪市"},
	}, true)
	assert.NoError(t, err)
	assert.Nil(t, cityIDs)
	assert.NotNil(t, residence)
	assert.Empty(t, commutingAreas)
	assert.Len(t, workLocations, 1)
}

func TestJobSpecificResolver_ResolveLocations_WorkLocationLookupError(t *testing.T) {
	cache := &master.Cache{
		PrefectureCities: master.PrefectureCities{
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("大阪市"), CityID: 10001},
		},
	}
	resolver := NewJobSpecificSearchResolver(
		newCacheServiceWithCache(cache),
		newLocationLookupServiceWithCache(cache, map[int][]*master.PrefectureCity{}),
	)
	_, _, _, _, err := resolver.ResolveLocations([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "存在しない都道府県", CityName: "存在しない市"},
	}, false)
	assert.Error(t, err)
}

func TestJobSpecificResolver_ResolveLocations_ExplicitCommutingAreasSkipResidenceLookup(t *testing.T) {
	cache := &master.Cache{
		PrefectureCities: master.PrefectureCities{
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("大阪市"), CityID: 10001},
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("堺市"), CityID: 10003},
			&master.PrefectureCity{PrefectureName: "大阪府", CityName: master.CityName("豊中市"), CityID: 10005},
		},
	}
	lookup := &countingLocationLookupStub{
		commutingResult: []int{10001},
	}
	resolver := NewJobSpecificSearchResolver(newCacheServiceWithCache(cache), lookup)

	cityIDs, residence, commutingAreas, workLocations, err := resolver.ResolveLocations([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "大阪府", CityName: "大阪市"},
		{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "大阪府", CityName: "堺市"},
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "大阪府", CityName: "豊中市"},
	}, false)
	assert.NoError(t, err)
	assert.NotNil(t, residence)
	assert.Len(t, commutingAreas, 1)
	assert.Len(t, workLocations, 1)
	assert.ElementsMatch(t, []int32{10003, 10005}, cityIDs)
	assert.Equal(t, 0, lookup.commutingCalls)
	// 明示的な通勤圏も希望勤務地も、どちらも GetCityIDsFromWorkLocations を使って
	// city ID 解決する実装なので、このケースでは 2 回呼ばれる。
	assert.Equal(t, 2, lookup.workCalls)
}
