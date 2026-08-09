package filter

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	"encoding/json"
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
	"gorm.io/datatypes"
)

type stubJobSearchFilterRepository struct {
	current  *jobfilter.JobSearchFilter
	reloaded *jobfilter.JobSearchFilter
	raw      *datatypes.JSON
	upsert   datatypes.JSON
	getErr   error
	putErr   error
	getCalls int
}

type stubGenericLocationLookup struct {
	commutingResult []int
	err             error
	calls           int
}

func (s *stubGenericLocationLookup) GetCommutingAreasFromResidence(_ string, _ string) ([]int, error) {
	s.calls++
	if s.err != nil {
		return nil, s.err
	}
	return s.commutingResult, nil
}

type stubLocationRequestResolver struct {
	results []*address.LocationRequest
}

func (s *stubLocationRequestResolver) GetLocationRequestsFromCityIDs(_ []int32) []*address.LocationRequest {
	return s.results
}

func (s *stubJobSearchFilterRepository) GetTypedJobSearchFilterBySessionID(_ string) (*jobfilter.JobSearchFilter, error) {
	s.getCalls++
	if s.reloaded != nil && s.getCalls > 1 {
		return s.reloaded, s.getErr
	}
	return s.current, s.getErr
}

func (s *stubJobSearchFilterRepository) GetJobSearchFilterBySessionID(_ string) (*datatypes.JSON, error) {
	return s.raw, s.getErr
}

func (s *stubJobSearchFilterRepository) UpsertJobSearchFilter(_ string, jobSearchFilter datatypes.JSON) error {
	s.upsert = jobSearchFilter
	if s.putErr == nil {
		var persisted jobfilter.JobSearchFilter
		if err := json.Unmarshal(jobSearchFilter, &persisted); err == nil {
			s.current = &persisted
		}
	}
	return s.putErr
}

func TestJobSearchFilterService_PersistFromSearchInput_Merge(t *testing.T) {
	repo := &stubJobSearchFilterRepository{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "A", Value: "A"}, Selected: true}},
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "B", Value: "B"}}},
				},
			},
			Locations: &jobfilter.JobSearchFilterLocations{
				Residence: &jobfilter.JobSearchFilterResidence{
					Address:        &jobfilter.JobSearchFilterAddress{PrefectureName: "旧", CityName: "住所"},
					CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{{Label: "東京都新宿区", PrefectureName: "東京都", CityName: "新宿区", Selected: true}},
				},
				WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区"}},
			},
		},
	}

	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
	persisted, err := service.PersistFromSearchInput("s1", &pcontracts.JobSpecificSearchInput{
		JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
		JobTypeNames:   []string{"B", "C"},
		Salary:         400,
		Locations: []*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "東京都", CityName: "渋谷区"},
		},
		Custom: &jobSpecificParams.ITEngineerParams{PositionKeyword: "go"},
	}, nil, &jobfilter.JobSearchFilter{
		SelectedOtherFilterOptions: map[string]map[string][]string{
			pcontracts.ToolNameSearchJobPostingsForITEngineer: {"言語（all）": {"Go"}},
		},
	})
	assert.NoError(t, err)
	assert.NotEmpty(t, repo.upsert)
	if assert.NotNil(t, persisted) {
		group := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostingsForITEngineer]
		if assert.Len(t, group, 3) {
			assert.False(t, group[0].Selected)
			assert.True(t, group[1].Selected)
			assert.True(t, group[2].Selected)
		}
		if assert.NotNil(t, persisted.PositionKeyword) {
			assert.Equal(t, "go", *persisted.PositionKeyword)
		}
		assert.Equal(t, []string{"go"}, persisted.SelectedOtherFilterOptions[pcontracts.SelectedFilterOptionsCommonKey]["PositionKeyword"])
	}

	var raw jobfilter.JobSearchFilter
	assert.NoError(t, json.Unmarshal(repo.upsert, &raw))
	if assert.NotNil(t, raw.PositionKeyword) {
		assert.Equal(t, "go", *raw.PositionKeyword)
	}
	assert.Equal(t, []string{"go"}, raw.SelectedOtherFilterOptions[pcontracts.SelectedFilterOptionsCommonKey]["PositionKeyword"])
}

func TestJobSearchFilterService_PersistFromGenericSearchParams(t *testing.T) {
	repo := &stubJobSearchFilterRepository{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostings: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "SE", Value: "SE"}, Selected: false}},
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "データ分析", Value: "データ分析"}, Selected: true}},
				},
			},
			Locations: &jobfilter.JobSearchFilterLocations{
				Residence: &jobfilter.JobSearchFilterResidence{
					Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
					CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{
						{Label: "東京都新宿区", PrefectureName: "東京都", CityName: "新宿区", Selected: true},
					},
				},
				WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{
					{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
				},
			},
		},
	}
	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)

	persisted, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"SE", "SE", "ITコンサルタント（アプリ）"},
			Salary:       600,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_FULL_REMOTE_WORK},
				{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "渋谷区"},
				{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "東京都", CityName: "渋谷区"},
			},
		},
		PositionKeyword: "go",
	})
	assert.NoError(t, err)
	assert.NotNil(t, persisted)
	group := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostings]
	assert.Len(t, group, 3)
	assert.True(t, group[0].Selected)
	assert.False(t, group[1].Selected)
	assert.True(t, group[2].Selected)
	assert.Equal(t, 600, persisted.Salary)
	if assert.NotNil(t, persisted.PositionKeyword) {
		assert.Equal(t, "go", *persisted.PositionKeyword)
	}
	assert.Equal(t, "go", persisted.SelectedOtherFilterOptions[pcontracts.SelectedFilterOptionsCommonKey]["PositionKeyword"][0])
	if assert.NotNil(t, persisted.Locations) {
		if assert.NotNil(t, persisted.Locations.Residence) {
			assert.Nil(t, persisted.Locations.Residence.Address)
			if assert.Len(t, persisted.Locations.Residence.CommutingAreas, 2) {
				assert.False(t, persisted.Locations.Residence.CommutingAreas[0].Selected)
				assert.True(t, persisted.Locations.Residence.CommutingAreas[1].Selected)
				assert.Equal(t, "東京都渋谷区", persisted.Locations.Residence.CommutingAreas[1].Label)
			}
		}
		if assert.Len(t, persisted.Locations.WorkLocations, 2) {
			assert.False(t, persisted.Locations.WorkLocations[0].Selected)
			assert.True(t, persisted.Locations.WorkLocations[1].Selected)
		}
	}
	assert.NotEmpty(t, repo.upsert)

	var raw jobfilter.JobSearchFilter
	assert.NoError(t, json.Unmarshal(repo.upsert, &raw))
	if assert.NotNil(t, raw.PositionKeyword) {
		assert.Equal(t, "go", *raw.PositionKeyword)
	}
	if assert.NotNil(t, raw.Locations) {
		if assert.NotNil(t, raw.Locations.Residence) {
			assert.Nil(t, raw.Locations.Residence.Address)
			if assert.Len(t, raw.Locations.Residence.CommutingAreas, 2) {
				assert.False(t, raw.Locations.Residence.CommutingAreas[0].Selected)
				assert.True(t, raw.Locations.Residence.CommutingAreas[1].Selected)
				assert.Equal(t, "東京都渋谷区", raw.Locations.Residence.CommutingAreas[1].Label)
			}
		}
		if assert.Len(t, raw.Locations.WorkLocations, 2) {
			assert.Equal(t, "東京都港区", raw.Locations.WorkLocations[0].Label)
			assert.False(t, raw.Locations.WorkLocations[0].Selected)
			assert.Equal(t, "東京都渋谷区", raw.Locations.WorkLocations[1].Label)
			assert.True(t, raw.Locations.WorkLocations[1].Selected)
		}
	}
}

func TestJobSearchFilterService_PersistFromGenericSearchParams_DerivesCommutingAreasFromResidence(t *testing.T) {
	repo := &stubJobSearchFilterRepository{}
	lookup := &stubGenericLocationLookup{commutingResult: []int{13104, 13113}}
	resolver := &stubLocationRequestResolver{
		results: []*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "新宿区"},
			{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "渋谷区"},
		},
	}
	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo).WithGenericLocationPersistence(lookup, resolver)

	persisted, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"SE"},
			Salary:       600,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
	})
	assert.NoError(t, err)
	assert.Equal(t, 1, lookup.calls)
	if assert.NotNil(t, persisted) && assert.NotNil(t, persisted.Locations) && assert.NotNil(t, persisted.Locations.Residence) {
		if assert.NotNil(t, persisted.Locations.Residence.Address) {
			assert.Equal(t, "東京都", persisted.Locations.Residence.Address.PrefectureName)
			assert.Equal(t, "新宿区", persisted.Locations.Residence.Address.CityName)
		}
		if assert.Len(t, persisted.Locations.Residence.CommutingAreas, 2) {
			assert.Equal(t, "東京都新宿区", persisted.Locations.Residence.CommutingAreas[0].Label)
			assert.Equal(t, "東京都渋谷区", persisted.Locations.Residence.CommutingAreas[1].Label)
			assert.True(t, persisted.Locations.Residence.CommutingAreas[0].Selected)
			assert.True(t, persisted.Locations.Residence.CommutingAreas[1].Selected)
		}
	}

	var raw jobfilter.JobSearchFilter
	assert.NoError(t, json.Unmarshal(repo.upsert, &raw))
	if assert.NotNil(t, raw.Locations) && assert.NotNil(t, raw.Locations.Residence) {
		if assert.Len(t, raw.Locations.Residence.CommutingAreas, 2) {
			assert.Equal(t, "東京都新宿区", raw.Locations.Residence.CommutingAreas[0].Label)
			assert.Equal(t, "東京都渋谷区", raw.Locations.Residence.CommutingAreas[1].Label)
		}
	}
}

func TestJobSearchFilterService_PersistFromGenericSearchParams_SkipsDerivedCommutingAreasWhenExplicitOnesExist(t *testing.T) {
	repo := &stubJobSearchFilterRepository{}
	lookup := &stubGenericLocationLookup{commutingResult: []int{13104}}
	resolver := &stubLocationRequestResolver{
		results: []*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "新宿区"},
		},
	}
	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo).WithGenericLocationPersistence(lookup, resolver)

	persisted, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"SE"},
			Salary:       600,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
				{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "港区"},
			},
		},
	})
	assert.NoError(t, err)
	assert.Equal(t, 0, lookup.calls)
	if assert.NotNil(t, persisted) && assert.NotNil(t, persisted.Locations) && assert.NotNil(t, persisted.Locations.Residence) {
		if assert.Len(t, persisted.Locations.Residence.CommutingAreas, 1) {
			assert.Equal(t, "東京都港区", persisted.Locations.Residence.CommutingAreas[0].Label)
		}
	}
}

func TestJobSearchFilterService_PersistFromGenericSearchParams_FallsBackWhenDerivedCommutingLookupFails(t *testing.T) {
	repo := &stubJobSearchFilterRepository{}
	lookup := &stubGenericLocationLookup{err: errors.New("lookup failed")}
	resolver := &stubLocationRequestResolver{
		results: []*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "新宿区"},
		},
	}
	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo).WithGenericLocationPersistence(lookup, resolver)

	persisted, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"SE"},
			Salary:       600,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
	})
	assert.NoError(t, err)
	assert.Equal(t, 1, lookup.calls)
	if assert.NotNil(t, persisted) && assert.NotNil(t, persisted.Locations) && assert.NotNil(t, persisted.Locations.Residence) {
		if assert.NotNil(t, persisted.Locations.Residence.Address) {
			assert.Equal(t, "東京都", persisted.Locations.Residence.Address.PrefectureName)
			assert.Equal(t, "新宿区", persisted.Locations.Residence.Address.CityName)
		}
		assert.Empty(t, persisted.Locations.Residence.CommutingAreas)
	}

	var raw jobfilter.JobSearchFilter
	assert.NoError(t, json.Unmarshal(repo.upsert, &raw))
	if assert.NotNil(t, raw.Locations) && assert.NotNil(t, raw.Locations.Residence) {
		if assert.NotNil(t, raw.Locations.Residence.Address) {
			assert.Equal(t, "東京都", raw.Locations.Residence.Address.PrefectureName)
			assert.Equal(t, "新宿区", raw.Locations.Residence.Address.CityName)
		}
		assert.Empty(t, raw.Locations.Residence.CommutingAreas)
	}
}

func TestBuildGenericLocations_PreservesExplicitCommutingAreasSeparatelyFromWorkLocations(t *testing.T) {
	got := buildGenericLocations([]*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "東京都", CityName: "新宿区"},
		{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "渋谷区"},
		{LocationType: address.LOCATION_TYPE_WORK_LOCATION, PrefectureName: "東京都", CityName: "港区"},
	})

	if assert.NotNil(t, got) {
		if assert.NotNil(t, got.Residence) {
			if assert.NotNil(t, got.Residence.Address) {
				assert.Equal(t, "東京都", got.Residence.Address.PrefectureName)
				assert.Equal(t, "新宿区", got.Residence.Address.CityName)
			}
			if assert.Len(t, got.Residence.CommutingAreas, 1) {
				assert.Equal(t, "東京都渋谷区", got.Residence.CommutingAreas[0].Label)
			}
		}
		if assert.Len(t, got.WorkLocations, 1) {
			assert.Equal(t, "東京都港区", got.WorkLocations[0].Label)
		}
	}
}

func TestJobSearchFilterService_PersistFromSearchInput_Branches(t *testing.T) {
	t.Run("セッションIDが空の場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		_, err := service.PersistFromSearchInput("", &pcontracts.JobSpecificSearchInput{}, nil, nil)
		assert.NoError(t, err)
		assert.Empty(t, repo.upsert)
	})

	t.Run("取得時にリポジトリがエラーを返す場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{getErr: errors.New("get failed")}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		_, err := service.PersistFromSearchInput("s1", &pcontracts.JobSpecificSearchInput{}, nil, nil)
		assert.Error(t, err)
	})

	t.Run("保存時にリポジトリがエラーを返す場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{current: nil, putErr: errors.New("upsert failed")}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		_, err := service.PersistFromSearchInput("s1", &pcontracts.JobSpecificSearchInput{JobTypeNames: []string{"X"}, Salary: 100}, nil, nil)
		assert.Error(t, err)
	})

	t.Run("marshalでエラーになる場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		service.marshal = func(_ any) ([]byte, error) { return nil, errors.New("marshal failed") }
		_, err := service.PersistFromSearchInput("s1", &pcontracts.JobSpecificSearchInput{}, nil, nil)
		assert.Error(t, err)
	})

	t.Run("汎用検索でセッションIDが空の場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		_, err := service.PersistFromGenericSearchParams("", &pmodel.GenericPositionSearchParams{})
		assert.NoError(t, err)
		assert.Empty(t, repo.upsert)
	})

	t.Run("汎用検索でmarshalがエラーになる場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		service.marshal = func(_ any) ([]byte, error) { return nil, errors.New("marshal failed") }
		_, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{})
		assert.Error(t, err)
	})

	t.Run("汎用検索で保存時にリポジトリがエラーを返す場合", func(t *testing.T) {
		repo := &stubJobSearchFilterRepository{putErr: errors.New("upsert failed")}
		service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
		_, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{})
		assert.Error(t, err)
	})
}

func TestJobSearchFilterService_PersistFromGenericSearchParams_FullRemoteWithExistingFilter(t *testing.T) {
	repo := &stubJobSearchFilterRepository{
		current: &jobfilter.JobSearchFilter{
			Locations: &jobfilter.JobSearchFilterLocations{
				WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{
					{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
				},
				RemoteWorkPossible: nil,
			},
		},
	}
	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)

	persisted, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			JobtypeNames: []string{"SE"},
			Salary:       600,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_FULL_REMOTE_WORK},
			},
		},
	})
	assert.NoError(t, err)
	if assert.NotNil(t, persisted) && assert.NotNil(t, persisted.Locations) {
		if assert.Len(t, persisted.Locations.WorkLocations, 1) {
			assert.Equal(t, "東京都港区", persisted.Locations.WorkLocations[0].Label)
			assert.False(t, persisted.Locations.WorkLocations[0].Selected)
		}
		if assert.NotNil(t, persisted.Locations.RemoteWorkPossible) {
			assert.True(t, *persisted.Locations.RemoteWorkPossible)
		}
	}

	var raw jobfilter.JobSearchFilter
	assert.NoError(t, json.Unmarshal(repo.upsert, &raw))
	if assert.NotNil(t, raw.Locations) {
		if assert.Len(t, raw.Locations.WorkLocations, 1) {
			assert.Equal(t, "東京都港区", raw.Locations.WorkLocations[0].Label)
			assert.False(t, raw.Locations.WorkLocations[0].Selected)
		}
		if assert.NotNil(t, raw.Locations.RemoteWorkPossible) {
			assert.True(t, *raw.Locations.RemoteWorkPossible)
		}
	}
}

func TestJobSearchFilterService_PersistFromGenericSearchParams_UsesCurrentLocationsWhenRequestHasNoUsableLocations(t *testing.T) {
	repo := &stubJobSearchFilterRepository{
		current: &jobfilter.JobSearchFilter{
			Locations: &jobfilter.JobSearchFilterLocations{
				Residence: &jobfilter.JobSearchFilterResidence{
					Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
					CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{
						{Label: "東京都新宿区", PrefectureName: "東京都", CityName: "新宿区", Selected: true},
					},
				},
				WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{
					{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
				},
			},
		},
	}

	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
	persisted, err := service.PersistFromGenericSearchParams("s1", &pmodel.GenericPositionSearchParams{
		CommonPositionSearchParams: pmodel.CommonPositionSearchParams{
			Salary: 600,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_WORK_LOCATION},
				nil,
			},
		},
	})
	assert.NoError(t, err)
	if assert.NotNil(t, persisted) && assert.NotNil(t, persisted.Locations) {
		if assert.NotNil(t, persisted.Locations.Residence) && assert.NotNil(t, persisted.Locations.Residence.Address) {
			assert.Equal(t, "東京都", persisted.Locations.Residence.Address.PrefectureName)
			assert.Equal(t, "新宿区", persisted.Locations.Residence.Address.CityName)
		}
		if assert.Len(t, persisted.Locations.WorkLocations, 1) {
			assert.Equal(t, "東京都港区", persisted.Locations.WorkLocations[0].Label)
			assert.True(t, persisted.Locations.WorkLocations[0].Selected)
		}
	}
}

func TestJobSearchFilterService_PersistFromSearchInput_ReloadsHydratedDescriptions(t *testing.T) {
	repo := &stubJobSearchFilterRepository{
		current: &jobfilter.JobSearchFilter{},
		reloaded: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					{
						JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
							JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
								Label: "情報システム（業務）",
								Value: "情報システム（業務）",
							},
							Selected: true,
						},
						Description: "社内業務システムの企画・運用を担う職種です。",
					},
				},
			},
			SelectedOtherFilterOptions: map[string]map[string][]string{},
		},
	}

	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
	persisted, err := service.PersistFromSearchInput("s1", &pcontracts.JobSpecificSearchInput{
		JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
		JobTypeNames:   []string{"情報システム（業務）"},
		Salary:         400,
	}, nil, &jobfilter.JobSearchFilter{})
	assert.NoError(t, err)
	if assert.NotNil(t, persisted) {
		group := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostingsForITEngineer]
		if assert.Len(t, group, 1) {
			assert.Equal(t, "社内業務システムの企画・運用を担う職種です。", group[0].Description)
		}
	}
}

func TestJobSearchFilterService_PersistFromSearchInput_DropsCommutingAreasWithoutResidence(t *testing.T) {
	repo := &stubJobSearchFilterRepository{
		current: &jobfilter.JobSearchFilter{},
	}

	service := NewJobSearchFilterService(&tmock.MockLogger{}, repo)
	persisted, err := service.PersistFromSearchInput("s1", &pcontracts.JobSpecificSearchInput{
		JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
		JobTypeNames:   []string{"情報システム（業務）"},
		Salary:         400,
		Locations: []*address.LocationRequest{
			{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "新宿区"},
		},
	}, []*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "新宿区"},
	}, &jobfilter.JobSearchFilter{})
	assert.NoError(t, err)
	if assert.NotNil(t, persisted) {
		assert.Nil(t, persisted.Locations)
	}

	var raw jobfilter.JobSearchFilter
	assert.NoError(t, json.Unmarshal(repo.upsert, &raw))
	assert.Nil(t, raw.Locations)
}

func TestMergeRequestedJobTypeGroups_SelectedGroupMergedOnce(t *testing.T) {
	current := map[string][]*jobfilter.JobtypeSelectableItem{
		pcontracts.ToolNameSearchJobPostingsForITEngineer: {
			{
				JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
					JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "A", Value: "A"},
					Selected:                         false,
				},
			},
			{
				JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
					JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "B", Value: "B"},
					Selected:                         false,
				},
			},
		},
	}

	merged := mergeRequestedJobTypeGroups(
		current,
		pcontracts.ToolNameSearchJobPostingsForITEngineer,
		map[string][]string{
			pcontracts.ToolNameSearchJobPostingsForITEngineer: {"B", "C"},
		},
	)

	group := merged[pcontracts.ToolNameSearchJobPostingsForITEngineer]
	if assert.Len(t, group, 3) {
		assert.Equal(t, "A", group[0].Value)
		assert.False(t, group[0].Selected)
		assert.Equal(t, "B", group[1].Value)
		assert.True(t, group[1].Selected)
		assert.Equal(t, "C", group[2].Value)
		assert.True(t, group[2].Selected)
	}
}
