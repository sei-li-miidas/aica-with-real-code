package position

import (
	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	psupport "aica/api/api/mcptool/usecase/position/support"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	uaposition "aica/api/domain/user/apply/position"
	"errors"
	"miidas/m2/user/marketvalue/grpc/iface"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

type readerStub struct {
	get func(sessionID string) (*jobfilter.JobSearchFilter, error)
}

func (r *readerStub) GetBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error) {
	return r.get(sessionID)
}

type searchExtensionWithFilters struct {
	name    string
	options []string
}

func (e *searchExtensionWithFilters) ApplyMV2(_ *iface.Company, _ *iface.Business, _ *iface.Position) {
}

func (e *searchExtensionWithFilters) BuildSelectedOtherFilterOptions() (string, []string) {
	return e.name, e.options
}

func (e *searchExtensionWithFilters) RemoteWorkPossible() bool { return false }

func (e *searchExtensionWithFilters) Keyword() string { return "" }

func TestSearchWithJobType_ExecuteWithThemeBySession_AndHelpers(t *testing.T) {
	uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, nil, nil)
	_, _, err := uc.ExecuteWithThemeBySession("", master.JobTypeLargeIDITSpecialist, pcontracts.THEME_HIGH_SALARY)
	assert.Error(t, err)

	uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, nil, nil)
	_, _, err = uc.ExecuteWithThemeBySession("s", master.JobTypeLargeIDITSpecialist, pcontracts.THEME_HIGH_SALARY)
	assert.Error(t, err)

	uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, &readerStub{
		get: func(sessionID string) (*jobfilter.JobSearchFilter, error) {
			return &jobfilter.JobSearchFilter{}, nil
		},
	}, nil)
	_, _, err = uc.ExecuteWithThemeBySession("s", master.JobTypeLargeIDITSpecialist, pcontracts.THEME_HIGH_SALARY)
	assert.Error(t, err)

	assert.Equal(t, []string{"A", "B"}, selectedJobTypeNames(map[string][]*jobfilter.JobtypeSelectableItem{
		pcontracts.ToolNameSearchJobPostingsForITEngineer: {
			{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
				JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Value: "A"},
				Selected:                         true,
			}},
			{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
				JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Value: "B"},
				Selected:                         true,
			}},
		},
	}, pcontracts.ToolNameSearchJobPostingsForITEngineer))
	assert.Equal(t, []string{"A", "B"}, psupport.RequestedJobTypeNames(&pcontracts.JobSpecificSearchInput{JobTypeNames: []string{"A", "B", "A"}}))

	assert.Nil(t, toSelectableItemsFromLocations(nil))
	assert.Empty(t, toSelectableItemsFromLocations([]*address.LocationRequest{{}}))
	items := toSelectableItemsFromLocations([]*address.LocationRequest{{
		PrefectureName: "東京都",
		CityName:       "新宿区",
	}})
	assert.Len(t, items, 1)
	assert.Equal(t, "東京都新宿区", items[0].Label)
}

func TestSearchWithJobType_BuildInputAndCustomHelpers(t *testing.T) {
	uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, &testResolver{
		resolveIDs: func(names []string) ([]int32, error) { return []int32{1}, nil },
	}, nil, nil)

	_, err := uc.buildInputFromStoredFilter(nil, master.JobTypeLargeIDITSpecialist)
	assert.Error(t, err)

	filter := &jobfilter.JobSearchFilter{
		Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
			pcontracts.ToolNameSearchJobPostingsForITEngineer: {
				{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
					JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Value: "ITコンサルタント（アプリ）"},
					Selected:                         true,
				}},
				{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
					JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Value: "Webアプリ開発"},
					Selected:                         true,
				}},
			},
		},
		Salary:          500,
		PositionKeyword: psupport.StringPtrIfNonEmpty("backend"),
		Locations: &jobfilter.JobSearchFilterLocations{
			Residence: &jobfilter.JobSearchFilterResidence{
				Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
			},
		},
		SelectedOtherFilterOptions: map[string]map[string][]string{
			pcontracts.ToolNameSearchJobPostingsForITEngineer: {"言語（all）": {"Go"}},
		},
	}
	input, err := uc.buildInputFromStoredFilter(filter, master.JobTypeLargeIDITSpecialist)
	assert.NoError(t, err)
	assert.NotNil(t, input)
	assert.Equal(t, int32(500), input.Salary)
	assert.Equal(t, []string{"ITコンサルタント（アプリ）", "Webアプリ開発"}, input.JobTypeNames)
	itParams, ok := input.Custom.(*jobSpecificParams.ITEngineerParams)
	if assert.True(t, ok) {
		assert.Equal(t, "backend", itParams.PositionKeyword)
	}

	loc, err := uc.resolveLocationWithType("", address.LOCATION_TYPE_RESIDENCE)
	assert.NoError(t, err)
	assert.Nil(t, loc)

	loc, err = uc.resolveStoredLocationWithType(&jobfilter.JobSearchFilterLocationSelectableItem{
		Label:          "東京都渋谷区",
		PrefectureName: "東京都",
		CityName:       "渋谷区",
	}, address.LOCATION_TYPE_WORK_LOCATION)
	assert.NoError(t, err)
	assert.Equal(t, address.LOCATION_TYPE_WORK_LOCATION, loc.LocationType)

	custom, err := buildCustomParamsFromSelected(master.JobTypeLargeIDFinancialSpecialist, map[string][]string{}, nil)
	assert.NoError(t, err)
	assert.NotNil(t, custom)
	_, err = buildCustomParamsFromSelected(master.JobTypeLargeID(99), nil, nil)
	assert.Error(t, err)

	other := collectOtherFiltersFromExtensions([]pcontracts.SearchExtension{&mockSearchExtension{}})
	assert.Empty(t, other)
	assert.Nil(t, collectOtherFiltersFromExtensions(nil))

	other = collectOtherFiltersFromExtensions([]pcontracts.SearchExtension{
		&searchExtensionWithFilters{name: "", options: []string{"Go"}},
		&searchExtensionWithFilters{name: "   ", options: []string{"TypeScript"}},
		&searchExtensionWithFilters{name: "言語（all）", options: []string{"Go"}},
	})
	assert.NotContains(t, other, "")
	assert.NotContains(t, other, "   ")
	assert.Equal(t, []string{"Go"}, other["言語（all）"])
}

func TestJobSpecificResolver_BasicMethods(t *testing.T) {
	cp := &master.CacheProvider{}
	setMasterCacheProviderCache(cp, &master.Cache{
		Prefectures: master.Prefectures{{ID: 1, Name: "北海道"}},
		Cities:      master.Cities{{ID: 11002, Name: "札幌市", PrefectureID: 1}},
		PrefectureCities: master.PrefectureCities{
			{PrefectureID: 1, PrefectureName: "北海道", CityID: 11002, CityName: "札幌市", Name: "北海道札幌市"},
		},
		JobTypeSmalls: master.JobTypeSmalls{
			{ID: 1, Name: "ITコンサルタント（アプリ）"},
		},
		Skills: master.Skills{
			{ID: 1, Name: "Go"},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{TraitPositionID: master.PtjSalesStyleDive, Value: 1, Name: "あり", UserSideName: "あり"},
			},
		},
	})
	l := &tmock.MockLogger{}
	cache := service.NewMiidasCacheService(l, cp, service.NewProviderRepositoryRegistry(l))
	locationLookup := service.NewLocationLookupService(&tmock.MockLogger{}, cp, &testCommutingAreaSearcher{})
	r := NewJobSpecificSearchResolver(cache, locationLookup)
	impl := r.(*jobSpecificSearchResolverImpl)

	assert.True(t, impl.ExistsPrefectureCity("北海道", "札幌市"))
	loc, err := impl.ResolveLocationByName("北海道札幌市")
	assert.NoError(t, err)
	assert.NotNil(t, loc)
}

func TestSearchWithJobType_BuildLocationsFromStoredFilter_Branches(t *testing.T) {
	uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, nil, nil)
	locations, err := uc.buildLocationsFromStoredFilter(&jobfilter.JobSearchFilterLocations{})
	assert.NoError(t, err)
	assert.Nil(t, locations)

	resolver := new(mockJobSpecificSearchResolver)
	resolver.On("ResolveLocationByName", "北海道小樽市").Return(&address.LocationRequest{
		PrefectureName: "北海道",
		CityName:       "小樽市",
	}, nil).Once()
	uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, resolver, nil, nil)
	locations, err = uc.buildLocationsFromStoredFilter(&jobfilter.JobSearchFilterLocations{
		Residence: &jobfilter.JobSearchFilterResidence{
			Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "北海道", CityName: "札幌市"},
			CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{
				{Label: "未選択", Selected: false},
			},
		},
		WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{
			{Label: "北海道小樽市", Selected: true},
		},
	})
	assert.NoError(t, err)
	assert.Len(t, locations, 2)
	assert.Equal(t, address.LOCATION_TYPE_RESIDENCE, locations[0].LocationType)
	assert.Equal(t, address.LOCATION_TYPE_WORK_LOCATION, locations[1].LocationType)
	resolver.AssertExpectations(t)
}

func TestSearchWithJobType_ResolveLocationHelpers_ErrorBranches(t *testing.T) {
	resolver := new(mockJobSpecificSearchResolver)
	resolver.On("ResolveLocationByName", "bad").Return((*address.LocationRequest)(nil), errors.New("resolve failed")).Once()
	uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, resolver, nil, nil)

	loc, err := uc.resolveLocationWithType("bad", address.LOCATION_TYPE_RESIDENCE)
	assert.Error(t, err)
	assert.Nil(t, loc)
	resolver.AssertExpectations(t)

	resolver2 := new(mockJobSpecificSearchResolver)
	resolver2.On("ResolveLocationByName", "fallback").Return((*address.LocationRequest)(nil), errors.New("fallback failed")).Once()
	uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, resolver2, nil, nil)
	loc, err = uc.resolveStoredLocationWithType(&jobfilter.JobSearchFilterLocationSelectableItem{
		Label: "fallback",
	}, address.LOCATION_TYPE_WORK_LOCATION)
	assert.Error(t, err)
	assert.Nil(t, loc)
	resolver2.AssertExpectations(t)
}

func TestSearchWithJobType_ExecuteWithThemeBySession_SuccessPath(t *testing.T) {
	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockReadPositionRepo := new(mockReadPositionRepository)
	resolver := new(mockJobSpecificSearchResolver)

	mockMVGateway.
		On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
		Return([]*iface.PositionListEntry{{PositionId: 101}}, nil).
		Once()
	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{101}).Return(uaposition.Positions{
		{ID: 101},
	}, nil).Once()

	resolver.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32{1}, nil).Once()
	resolver.On("ResolveLocations", mock.Anything, false).Return([]int32{11002}, (*address.LocationRequest)(nil), []*address.LocationRequest{}, []*address.LocationRequest{}, nil).Once()
	resolver.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32{}, nil).Once()
	resolver.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(1), nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		mockLogger,
		mockMVGateway,
		nil,
		nil,
		mockReadPositionRepo,
		resolver,
		&readerStub{
			get: func(sessionID string) (*jobfilter.JobSearchFilter, error) {
				assert.Equal(t, "s", sessionID)
				return &jobfilter.JobSearchFilter{
					Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
						pcontracts.ToolNameSearchJobPostingsForITEngineer: {
							{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
								JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Value: "A"},
								Selected:                         true,
							}},
						},
					},
					Salary: 500,
					Locations: &jobfilter.JobSearchFilterLocations{
						Residence: &jobfilter.JobSearchFilterResidence{
							Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "北海道", CityName: "札幌市"},
						},
					},
					SelectedOtherFilterOptions: map[string]map[string][]string{
						pcontracts.ToolNameSearchJobPostingsForITEngineer: {},
					},
				}, nil
			},
		},
		nil,
	)

	ids, positions, err := uc.ExecuteWithThemeBySession("s", master.JobTypeLargeIDITSpecialist, pcontracts.THEME_HIGH_SALARY)
	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{101}, ids)
	assert.Equal(t, []*pmodel.PositionSummary{{ID: 101}}, positions)
	mockMVGateway.AssertExpectations(t)
	mockReadPositionRepo.AssertExpectations(t)
	resolver.AssertExpectations(t)
}
