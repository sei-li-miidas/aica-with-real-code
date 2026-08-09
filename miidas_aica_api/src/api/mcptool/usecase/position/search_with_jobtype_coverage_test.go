package position

// search_with_jobtype_coverage_test.go
//
// Unit tests for previously uncovered code paths in SearchWithJobTypeUseCase,
// identified as gaps during PR review.
//
// Test matrix:
//   1. Execute(): persistence success → returned filter is the persisted result
//   2. Execute(): persistence failure → search succeeds anyway (graceful degrade)
//   3. Execute(): nil persister → locally-built filter is returned
//   4. ExecuteWithThemeBySession(): happy path round-trip (session → rebuild → search)
//   5. buildLocationsFromStoredFilter(): commuting area falls back to label-resolver

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/public/master"
	uaposition "aica/api/domain/user/apply/position"
	"errors"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// persisterStub implements interfaces.JobSearchFilterPersister using a plain function.
type persisterStub struct {
	persist func(sessionID string, input *pcontracts.JobSpecificSearchInput, commutingAreas []*address.LocationRequest, searchFilters *jobfilter.JobSearchFilter) (*jobfilter.JobSearchFilter, error)
}

func (s *persisterStub) PersistFromSearchInput(
	sessionID string,
	input *pcontracts.JobSpecificSearchInput,
	commutingAreas []*address.LocationRequest,
	searchFilters *jobfilter.JobSearchFilter,
) (*jobfilter.JobSearchFilter, error) {
	return s.persist(sessionID, input, commutingAreas, searchFilters)
}

// sharedParityTestCache is the minimal master cache required for all parity tests.
var sharedParityTestCache = &master.Cache{
	Prefectures: master.Prefectures{
		{ID: 1, Name: "北海道"},
	},
	Cities: master.Cities{
		{ID: 11002, Name: "札幌市", PrefectureID: 1},
	},
	PrefectureCities: master.PrefectureCities{
		{PrefectureID: 1, PrefectureName: "北海道", CityID: 11002, CityName: "札幌市"},
	},
}

// sharedParityInput is a minimal valid IT-engineer search input reused across tests.
var sharedParityInput = &pcontracts.JobSpecificSearchInput{
	JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
	JobTypeNames:   []string{"ITコンサルタント（アプリ）"},
	Salary:         500,
	Locations: []*address.LocationRequest{
		{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
	},
	Custom: &mockJobSpecificParams{
		extensions: []pcontracts.SearchExtension{&mockSearchExtension{remote: false}},
	},
}

// newParityResolver builds a mock resolver with expectations for the shared input.
func newParityResolver(t *testing.T) *mockJobSpecificSearchResolver {
	t.Helper()
	r := new(mockJobSpecificSearchResolver)
	r.On("ResolveJobTypeSmallIDs", []string{"ITコンサルタント（アプリ）"}).Return([]int32{10001}, nil).Once()
	r.On("ResolveLocations", mock.Anything, false).Return(
		[]int32{11002},
		&address.LocationRequest{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
		[]*address.LocationRequest{},
		[]*address.LocationRequest{},
		nil,
	).Once()
	r.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), nil).Once()
	r.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(0), nil).Once()
	return r
}

// newParityMVAndRepo builds MV gateway + position repo mocks used across parity tests.
func newParityMVAndRepo(t *testing.T) (*mockMvGateway, *mockReadPositionRepository) {
	t.Helper()
	mv := new(mockMvGateway)
	mv.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
		Return([]*iface.PositionListEntry{{PositionId: 55}}, nil).Once()
	repo := new(mockReadPositionRepository)
	repo.On("GetByIDs", []uaposition.ID{55}).Return(uaposition.Positions{{ID: 55}}, nil).Once()
	return mv, repo
}

// --- Test 1 ---

// TestSearchWithJobTypeUseCase_Execute_PersistenceSuccessOverridesLocalFilter verifies
// that when PersistFromSearchInput returns a non-nil filter, Execute() returns that
// persisted filter rather than the locally-built one.
func TestSearchWithJobTypeUseCase_Execute_PersistenceSuccessOverridesLocalFilter(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), sharedParityTestCache)

	resolver := newParityResolver(t)
	mv, repo := newParityMVAndRepo(t)

	persistedFilter := &jobfilter.JobSearchFilter{Salary: 888}
	persister := &persisterStub{
		persist: func(_ string, _ *pcontracts.JobSpecificSearchInput, _ []*address.LocationRequest, _ *jobfilter.JobSearchFilter) (*jobfilter.JobSearchFilter, error) {
			return persistedFilter, nil
		},
	}

	uc := NewSearchWithJobTypeUseCase(
		&tmock.MockLogger{}, mv, nil, nil, repo, resolver, nil, persister,
	)

	ids, summaries, returnedFilter, err := uc.Execute("session-1", sharedParityInput)

	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{55}, ids)
	assert.Len(t, summaries, 1)
	assert.Equal(t, persistedFilter, returnedFilter,
		"persistence success: returned filter must be the persisted result, not the locally-built one")

	resolver.AssertExpectations(t)
	mv.AssertExpectations(t)
	repo.AssertExpectations(t)
}

// --- Test 2 ---

// TestSearchWithJobTypeUseCase_Execute_PersistenceFailureGracefullyDegraded verifies
// that when PersistFromSearchInput returns an error, Execute() still returns search
// results without propagating the error (graceful degrade with error logging).
func TestSearchWithJobTypeUseCase_Execute_PersistenceFailureGracefullyDegraded(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), sharedParityTestCache)

	resolver := newParityResolver(t)
	mv, repo := newParityMVAndRepo(t)

	persistErr := errors.New("database connection refused")
	persister := &persisterStub{
		persist: func(_ string, _ *pcontracts.JobSpecificSearchInput, _ []*address.LocationRequest, _ *jobfilter.JobSearchFilter) (*jobfilter.JobSearchFilter, error) {
			return nil, persistErr
		},
	}

	uc := NewSearchWithJobTypeUseCase(
		&tmock.MockLogger{}, mv, nil, nil, repo, resolver, nil, persister,
	)

	ids, summaries, returnedFilter, err := uc.Execute("session-1", sharedParityInput)

	assert.NoError(t, err,
		"persistence failure must not propagate as an error — Execute() should degrade gracefully")
	assert.Equal(t, []uaposition.ID{55}, ids,
		"search results must be returned even when persistence fails")
	assert.Len(t, summaries, 1)
	assert.NotNil(t, returnedFilter,
		"locally-built filter must be returned when persistence fails")
	assert.NotEqual(t, pmodel.PositionSummary{}, summaries[0])

	resolver.AssertExpectations(t)
	mv.AssertExpectations(t)
	repo.AssertExpectations(t)
}

// --- Test 3 ---

// TestSearchWithJobTypeUseCase_Execute_NilPersisterReturnsLocallyBuiltFilter verifies
// that when no persister is configured, Execute() uses the locally-built search filter.
func TestSearchWithJobTypeUseCase_Execute_NilPersisterReturnsLocallyBuiltFilter(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), sharedParityTestCache)

	resolver := newParityResolver(t)
	mv, repo := newParityMVAndRepo(t)

	// persister = nil (reader = nil, persister = nil)
	uc := NewSearchWithJobTypeUseCase(
		&tmock.MockLogger{}, mv, nil, nil, repo, resolver, nil, nil,
	)

	ids, summaries, returnedFilter, err := uc.Execute("session-1", sharedParityInput)

	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{55}, ids)
	assert.Len(t, summaries, 1)
	assert.NotNil(t, returnedFilter, "locally-built filter must be returned when persister is nil")
	assert.Equal(t, 500, returnedFilter.Salary,
		"locally-built filter salary must match input salary")

	resolver.AssertExpectations(t)
	mv.AssertExpectations(t)
	repo.AssertExpectations(t)
}

// --- Test 4 ---

// TestSearchWithJobTypeUseCase_ExecuteWithThemeBySession_HappyPath verifies the full
// round-trip: read stored filter → reconstruct input → execute theme search → return
// position IDs and summaries. This is the primary regression guard for
// recommendation endpoints.
func TestSearchWithJobTypeUseCase_ExecuteWithThemeBySession_HappyPath(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), sharedParityTestCache)

	// Stored filter representing a previous IT-engineer search session.
	storedFilter := &jobfilter.JobSearchFilter{
		Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
			pcontracts.ToolNameSearchJobPostingsForITEngineer: {
				{
					JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
						JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{
							Label: "ITコンサルタント（アプリ）",
							Value: "ITコンサルタント（アプリ）",
						},
						Selected: true,
					},
				},
			},
		},
		Salary: 600,
		Locations: &jobfilter.JobSearchFilterLocations{
			Residence: &jobfilter.JobSearchFilterResidence{
				Address: &jobfilter.JobSearchFilterAddress{
					PrefectureName: "北海道",
					CityName:       "札幌市",
				},
			},
		},
	}

	reader := &readerStub{
		get: func(sessionID string) (*jobfilter.JobSearchFilter, error) {
			assert.Equal(t, "session-99", sessionID)
			return storedFilter, nil
		},
	}

	// resolver must handle the rebuilt-from-filter input (no selected skills → no ResolveSkills call).
	resolver := new(mockJobSpecificSearchResolver)
	resolver.On("ResolveJobTypeSmallIDs", []string{"ITコンサルタント（アプリ）"}).Return([]int32{10001}, nil).Once()
	resolver.On("ResolveLocations", mock.Anything, false).Return(
		[]int32{11002},
		&address.LocationRequest{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
		[]*address.LocationRequest{},
		[]*address.LocationRequest{},
		nil,
	).Once()
	resolver.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), nil).Once()
	resolver.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(0), nil).Once()

	mv := new(mockMvGateway)
	mv.On("GetWillPositionList",
		mock.Anything,
		mock.Anything,
		mock.MatchedBy(func(p *iface.Position) bool {
			return p.Job != nil &&
				p.Job.Importance == 3 &&
				len(p.Job.Value.Larges) == 1 &&
				p.Job.Value.Larges[0] == int32(master.JobTypeLargeIDITSpecialist)
		}),
	).Return([]*iface.PositionListEntry{{PositionId: 77}, {PositionId: 88}}, nil).Once()

	repo := new(mockReadPositionRepository)
	repo.On("GetByIDs", []uaposition.ID{77, 88}).Return(uaposition.Positions{{ID: 77}, {ID: 88}}, nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		&tmock.MockLogger{}, mv, nil, nil, repo, resolver, reader, nil,
	)

	ids, summaries, err := uc.ExecuteWithThemeBySession(
		"session-99",
		master.JobTypeLargeIDITSpecialist,
		pcontracts.THEME_HIGH_SALARY,
	)

	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{77, 88}, ids)
	assert.Len(t, summaries, 2)

	resolver.AssertExpectations(t)
	mv.AssertExpectations(t)
	repo.AssertExpectations(t)
}

// --- Test 5 ---

// TestSearchWithJobTypeUseCase_buildLocationsFromStoredFilter_CommutingAreaLabelFallback
// verifies that when a commuting area entry has no explicit city/prefecture names
// (only a Label), buildLocationsFromStoredFilter falls back to
// resolver.ResolveLocationByName to construct the LocationRequest.
func TestSearchWithJobTypeUseCase_buildLocationsFromStoredFilter_CommutingAreaLabelFallback(t *testing.T) {
	resolvedLocation := &address.LocationRequest{
		PrefectureName: "東京都",
		CityName:       "新宿区",
	}

	resolver := new(mockJobSpecificSearchResolver)
	resolver.On("ResolveLocationByName", "東京都新宿区").Return(resolvedLocation, nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		&tmock.MockLogger{}, nil, nil, nil, nil, resolver, nil, nil,
	)

	storedLocations := &jobfilter.JobSearchFilterLocations{
		Residence: &jobfilter.JobSearchFilterResidence{
			CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{
				{
					// No PrefectureName/CityName set — only Label → must fall back to resolver.
					Label:    "東京都新宿区",
					Selected: true,
				},
			},
		},
	}

	results, err := uc.buildLocationsFromStoredFilter(storedLocations)

	assert.NoError(t, err)
	assert.Len(t, results, 1)
	assert.Equal(t, address.LOCATION_TYPE_COMMUTING_AREAS, results[0].LocationType,
		"label-fallback path must assign LOCATION_TYPE_COMMUTING_AREAS")
	assert.Equal(t, "東京都", results[0].PrefectureName)
	assert.Equal(t, "新宿区", results[0].CityName)

	resolver.AssertExpectations(t)
}
