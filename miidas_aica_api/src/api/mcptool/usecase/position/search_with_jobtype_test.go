package position

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pfilter "aica/api/api/mcptool/usecase/position/filter"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	"aica/api/domain/position"
	"aica/api/domain/public/master"
	uaposition "aica/api/domain/user/apply/position"
	merr "aica/api/sdk/error"
	"aica/api/sdk/http"
	"errors"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/pgvector/pgvector-go"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"gorm.io/datatypes"
)

type mockJobSpecificSearchResolver struct {
	mock.Mock
}

func (m *mockJobSpecificSearchResolver) ExistsPrefectureCity(prefectureName string, cityName string) bool {
	return true
}

func (m *mockJobSpecificSearchResolver) ResolveJobTypeSmallIDs(names []string) ([]int32, error) {
	args := m.Called(names)
	return args.Get(0).([]int32), args.Error(1)
}
func (m *mockJobSpecificSearchResolver) ResolveLocations(locations []*address.LocationRequest, remoteWorkPossible bool) ([]int32, *address.LocationRequest, []*address.LocationRequest, []*address.LocationRequest, error) {
	args := m.Called(locations, remoteWorkPossible)
	return args.Get(0).([]int32), args.Get(1).(*address.LocationRequest), args.Get(2).([]*address.LocationRequest), args.Get(3).([]*address.LocationRequest), args.Error(4)
}
func (m *mockJobSpecificSearchResolver) ResolveLocationByName(name string) (*address.LocationRequest, error) {
	args := m.Called(name)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*address.LocationRequest), args.Error(1)
}
func (m *mockJobSpecificSearchResolver) ResolveSkills(skillNames []string) (master.Skills, error) {
	args := m.Called(skillNames)
	return args.Get(0).(master.Skills), args.Error(1)
}
func (m *mockJobSpecificSearchResolver) ResolveDayOffs(dayOffs *[]string) ([]int32, error) {
	args := m.Called(dayOffs)
	return args.Get(0).([]int32), args.Error(1)
}
func (m *mockJobSpecificSearchResolver) ResolveAverageOvertime(overtime *string) (int32, error) {
	args := m.Called(overtime)
	return args.Get(0).(int32), args.Error(1)
}
func (m *mockJobSpecificSearchResolver) ResolveSalesStyleDive(salesStyleDive *string) (int32, error) {
	args := m.Called(salesStyleDive)
	return args.Get(0).(int32), args.Error(1)
}

type mockJobSearchFilterRepo struct{ mock.Mock }

func (m *mockJobSearchFilterRepo) GetTypedJobSearchFilterBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error) {
	args := m.Called(sessionID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*jobfilter.JobSearchFilter), args.Error(1)
}
func (m *mockJobSearchFilterRepo) GetJobSearchFilterBySessionID(_ string) (*datatypes.JSON, error) {
	return nil, nil
}
func (m *mockJobSearchFilterRepo) UpsertJobSearchFilter(sessionID string, jobSearchFilter datatypes.JSON) error {
	args := m.Called(sessionID, jobSearchFilter)
	return args.Error(0)
}

type mockSearchExtension struct {
	remote  bool
	keyword string
}

func (e *mockSearchExtension) ApplyMV2(_ *iface.Company, _ *iface.Business, _ *iface.Position) {}
func (e *mockSearchExtension) BuildSelectedOtherFilterOptions() (string, []string) {
	return "", nil
}
func (e *mockSearchExtension) RemoteWorkPossible() bool { return e.remote }
func (e *mockSearchExtension) Keyword() string          { return e.keyword }

type mockJobSpecificParams struct {
	extensions []pcontracts.SearchExtension
}

func (p *mockJobSpecificParams) BuildExtensions(_ pcontracts.JobSpecificSearchResolver) ([]pcontracts.SearchExtension, error) {
	return p.extensions, nil
}

func (p *mockJobSpecificParams) SelectedOptionNamesByFilter() map[string]map[string]struct{} {
	return nil
}

func (p *mockJobSpecificParams) RemotePositionOptionState() *pcontracts.RemotePositionOptionState {
	return nil
}

func TestSearchWithJobTypeUseCase_Execute_NoKeyword(t *testing.T) {
	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockVectorizerRepo := new(mockVectorizerRepository)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)

	mockMVGateway.
		On(
			"GetWillPositionList",
			mock.Anything,
			mock.Anything,
			mock.MatchedBy(func(p *iface.Position) bool {
				return p.Job != nil && p.Job.Importance == 3 && len(p.Job.Value.Larges) == 1 && p.Job.Value.Larges[0] == int32(master.JobTypeLargeIDITSpecialist)
			}),
		).
		Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).
		Once()

	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{101, 102}).Return(uaposition.Positions{
		{ID: 101},
		{ID: 102},
	}, nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		mockLogger,
		mockMVGateway,
		mockVectorizerRepo,
		mockPositionRepo,
		mockReadPositionRepo,
		nil,
		nil,
		nil,
	)

	allPositionIDs, positions, err := uc.executeSearch(&pcontracts.PositionSearchWill{
		JobTypeLargeID: int32(master.JobTypeLargeIDITSpecialist),
	}, "", "", nil)

	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{101, 102}, allPositionIDs)
	assert.Equal(t, []*pmodel.PositionSummary{{ID: 101}, {ID: 102}}, positions)
	mockMVGateway.AssertExpectations(t)
	mockReadPositionRepo.AssertExpectations(t)
}

func TestSearchWithJobTypeUseCase_Execute_WithKeywordRerankAndDedup(t *testing.T) {
	embedding := pgvector.NewVector([]float32{0.1, 0.2, 0.3})

	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockVectorizerRepo := new(mockVectorizerRepository)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)

	mockMVGateway.
		On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
		Return([]*iface.PositionListEntry{{PositionId: 101}, {PositionId: 102}}, nil).
		Once()

	mockVectorizerRepo.On("GenerateEmbedding", "金融 営業").Return(&embedding, nil).Once()
	mockPositionRepo.On("SemanticSearch", embedding.String(), http.DEFAULT_DISTANCE, mock.Anything).
		Return([]*position.PositionSearchResult{
			{ID: 102, Distance: 0.1},
			{ID: 102, Distance: 0.11},
			{ID: 101, Distance: 0.2},
		}, nil).
		Once()
	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{102, 101}).Return(uaposition.Positions{
		{ID: 102},
		{ID: 101},
	}, nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		mockLogger,
		mockMVGateway,
		mockVectorizerRepo,
		mockPositionRepo,
		mockReadPositionRepo,
		nil,
		nil,
		nil,
	)

	allPositionIDs, positions, err := uc.executeSearch(&pcontracts.PositionSearchWill{
		JobTypeLargeID: int32(master.JobTypeLargeIDFinancialSpecialist),
	}, "金融 営業", "", nil)

	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{102, 101}, allPositionIDs)
	assert.Equal(t, []*pmodel.PositionSummary{{ID: 102}, {ID: 101}}, positions)
	mockMVGateway.AssertExpectations(t)
	mockVectorizerRepo.AssertExpectations(t)
	mockPositionRepo.AssertExpectations(t)
	mockReadPositionRepo.AssertExpectations(t)
}

func TestSearchWithJobTypeUseCase_Execute_MVGatewayCanceled(t *testing.T) {
	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockVectorizerRepo := new(mockVectorizerRepository)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)

	mockMVGateway.
		On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).
		Return([]*iface.PositionListEntry{}, status.Error(codes.Canceled, "request canceled")).
		Once()

	uc := NewSearchWithJobTypeUseCase(
		mockLogger,
		mockMVGateway,
		mockVectorizerRepo,
		mockPositionRepo,
		mockReadPositionRepo,
		nil,
		nil,
		nil,
	)

	_, _, err := uc.executeSearch(&pcontracts.PositionSearchWill{
		JobTypeLargeID: int32(master.JobTypeLargeIDITSpecialist),
	}, "", "", nil)

	assert.Error(t, err)
	assert.True(t, merr.Is(err, merr.ErrClientClosedRequest))
	mockMVGateway.AssertExpectations(t)
}

func TestSearchWithJobTypeUseCase_Execute_NonTheme(t *testing.T) {
	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockVectorizerRepo := new(mockVectorizerRepository)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)
	mockResolver := new(mockJobSpecificSearchResolver)
	mockProfileRepo := new(mockJobSearchFilterRepo)

	mockResolver.On("ResolveJobTypeSmallIDs", []string{"A", "B"}).Return([]int32{1, 2}, nil).Once()
	mockResolver.On("ResolveLocations", mock.Anything, true).Return([]int32{10}, (*address.LocationRequest)(nil), []*address.LocationRequest{}, []*address.LocationRequest{}, nil).Once()
	mockResolver.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), nil).Once()
	mockResolver.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(0), nil).Once()
	mockProfileRepo.On("GetTypedJobSearchFilterBySessionID", "session1").Return((*jobfilter.JobSearchFilter)(nil), nil).Twice()
	mockProfileRepo.On("UpsertJobSearchFilter", "session1", mock.Anything).Return(nil).Once()

	mockMVGateway.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).Return([]*iface.PositionListEntry{{PositionId: 101}}, nil).Once()
	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{101}).Return(uaposition.Positions{{ID: 101}}, nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		mockLogger,
		mockMVGateway,
		mockVectorizerRepo,
		mockPositionRepo,
		mockReadPositionRepo,
		mockResolver,
		pfilter.NewJobSearchFilterService(mockLogger, mockProfileRepo),
		pfilter.NewJobSearchFilterService(mockLogger, mockProfileRepo),
	)

	ids, rows, jobSearchFilter, err := uc.Execute("session1", &pcontracts.JobSpecificSearchInput{
		JobTypeNames:   []string{"A", "B"},
		Salary:         300,
		Locations:      []*address.LocationRequest{},
		JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
		Custom: &mockJobSpecificParams{
			extensions: []pcontracts.SearchExtension{
				&mockSearchExtension{remote: true},
			},
		},
	})
	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{101}, ids)
	assert.Equal(t, []*pmodel.PositionSummary{{ID: 101}}, rows)
	if assert.NotNil(t, jobSearchFilter) {
		group := jobSearchFilter.Jobtypes[pcontracts.ToolNameSearchJobPostingsForITEngineer]
		if assert.Len(t, group, 2) {
			assert.Equal(t, "A", group[0].Value)
			assert.Equal(t, "B", group[1].Value)
		}
	}
}

func TestSearchWithJobType_ExecuteWithTheme_AndHelpers(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), &master.Cache{
		Prefectures: master.Prefectures{
			&master.Prefecture{ID: 1, Name: "北海道"},
		},
		Cities: master.Cities{
			&master.City{ID: 11002, Name: "札幌市", PrefectureID: 1},
			&master.City{ID: 22001, Name: "未定義都道府県の市", PrefectureID: 2},
		},
		PrefectureCities: master.PrefectureCities{
			&master.PrefectureCity{PrefectureID: 1, PrefectureName: "北海道", CityID: 11002, CityName: "札幌市"},
		},
	})

	mockLogger := &tmock.MockLogger{}
	mockMVGateway := new(mockMvGateway)
	mockVectorizerRepo := new(mockVectorizerRepository)
	mockPositionRepo := new(mockPositionRepository)
	mockReadPositionRepo := new(mockReadPositionRepository)
	mockResolver := new(mockJobSpecificSearchResolver)

	mockResolver.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32{1}, nil).Once()
	mockResolver.On("ResolveLocations", mock.Anything, false).Return(
		[]int32{11002},
		&address.LocationRequest{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
		[]*address.LocationRequest{},
		[]*address.LocationRequest{},
		nil,
	).Once()
	mockResolver.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), nil).Once()
	mockResolver.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(0), nil).Once()

	mockMVGateway.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).Return([]*iface.PositionListEntry{{PositionId: 10}}, nil).Once()
	mockReadPositionRepo.On("GetByIDs", []uaposition.ID{10}).Return(uaposition.Positions{{ID: 10}}, nil).Once()

	uc := NewSearchWithJobTypeUseCase(
		mockLogger,
		mockMVGateway,
		mockVectorizerRepo,
		mockPositionRepo,
		mockReadPositionRepo,
		mockResolver,
		nil,
		nil,
	)

	ids, rows, err := uc.ExecuteWithTheme(
		&pcontracts.JobSpecificSearchInput{
			JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
			JobTypeNames:   []string{"A"},
			Salary:         300,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
			},
			Custom: &mockJobSpecificParams{
				extensions: []pcontracts.SearchExtension{
					&mockSearchExtension{remote: false},
				},
			},
		},
		pcontracts.THEME_HIGH_SALARY,
	)
	assert.NoError(t, err)
	assert.Equal(t, []uaposition.ID{10}, ids)
	assert.Len(t, rows, 1)

	mockResolver.AssertExpectations(t)
	mockMVGateway.AssertExpectations(t)
	mockReadPositionRepo.AssertExpectations(t)
}

func TestSearchWithJobType_ValidateInputAndExtractors(t *testing.T) {
	assert.Error(t, validateJobSpecificSearchInput(nil))
	assert.Error(t, validateJobSpecificSearchInput(&pcontracts.JobSpecificSearchInput{Salary: 0, Custom: &mockJobSpecificParams{}}))
	assert.Error(t, validateJobSpecificSearchInput(&pcontracts.JobSpecificSearchInput{Salary: 1, Custom: &mockJobSpecificParams{}}))
	assert.Error(t, validateJobSpecificSearchInput(&pcontracts.JobSpecificSearchInput{Salary: 1, JobTypeNames: []string{"A"}}))
	assert.NoError(t, validateJobSpecificSearchInput(&pcontracts.JobSpecificSearchInput{
		Salary:       1,
		JobTypeNames: []string{"A"},
		Custom:       &mockJobSpecificParams{},
	}))

	assert.False(t, extractRemoteWorkPossible(nil))
	assert.False(t, extractRemoteWorkPossible([]pcontracts.SearchExtension{&mockSearchExtension{remote: false}}))
	assert.True(t, extractRemoteWorkPossible([]pcontracts.SearchExtension{&mockSearchExtension{remote: true}}))

	assert.Equal(t, "", extractKeyword(nil))
	assert.Equal(t, "", extractKeyword([]pcontracts.SearchExtension{&mockSearchExtension{keyword: ""}}))
	assert.Equal(t, "go", extractKeyword([]pcontracts.SearchExtension{&mockSearchExtension{keyword: "go"}}))
}

type failingJobSpecificParams struct{}

func (f *failingJobSpecificParams) BuildExtensions(_ pcontracts.JobSpecificSearchResolver) ([]pcontracts.SearchExtension, error) {
	return nil, errors.New("build extensions failed")
}
func (f *failingJobSpecificParams) SelectedOptionNamesByFilter() map[string]map[string]struct{} {
	return nil
}
func (f *failingJobSpecificParams) RemotePositionOptionState() *pcontracts.RemotePositionOptionState {
	return nil
}

func TestSearchWithJobType_ExecuteAndExecuteByInput_ErrorPaths(t *testing.T) {
	setMasterCacheProviderCache(master.Provider(), &master.Cache{
		Prefectures: master.Prefectures{
			&master.Prefecture{ID: 1, Name: "北海道"},
		},
		Cities: master.Cities{
			&master.City{ID: 11002, Name: "札幌市", PrefectureID: 1},
		},
		PrefectureCities: master.PrefectureCities{
			&master.PrefectureCity{PrefectureID: 1, PrefectureName: "北海道", CityID: 11002, CityName: "札幌市"},
		},
	})

	t.Run("Executeが入力検証エラーを返す場合", func(t *testing.T) {
		uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, nil, nil)
		_, _, _, err := uc.Execute("sid", nil)
		assert.Error(t, err)
	})

	t.Run("拡張条件の構築に失敗する場合", func(t *testing.T) {
		uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, nil, nil)
		_, _, _, err := uc.executeByInput(&pcontracts.JobSpecificSearchInput{
			JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
			Salary:         1,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
			},
			Custom: &failingJobSpecificParams{},
		}, "")
		assert.Error(t, err)
	})

	t.Run("勤務地検証がリゾルバより前に失敗する場合", func(t *testing.T) {
		uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, nil, nil, nil)
		_, _, _, err := uc.executeByInput(&pcontracts.JobSpecificSearchInput{
			JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
			Salary:         1,
			Locations:      []*address.LocationRequest{},
			Custom: &mockJobSpecificParams{
				extensions: []pcontracts.SearchExtension{&mockSearchExtension{remote: false}},
			},
		}, "")
		assert.Error(t, err)
	})

	t.Run("各種リゾルバが失敗する場合", func(t *testing.T) {
		base := &pcontracts.JobSpecificSearchInput{
			JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
			Salary:         1,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
			},
			Custom: &mockJobSpecificParams{
				extensions: []pcontracts.SearchExtension{&mockSearchExtension{remote: false}},
			},
		}

		r1 := new(mockJobSpecificSearchResolver)
		r1.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32(nil), errors.New("jt failed")).Once()
		uc := NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, r1, nil, nil)
		_, _, _, err := uc.executeByInput(base, "")
		assert.Error(t, err)

		r2 := new(mockJobSpecificSearchResolver)
		r2.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32{1}, nil).Once()
		r2.On("ResolveLocations", mock.Anything, false).Return([]int32(nil), (*address.LocationRequest)(nil), []*address.LocationRequest(nil), []*address.LocationRequest(nil), errors.New("loc failed")).Once()
		uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, r2, nil, nil)
		_, _, _, err = uc.executeByInput(base, "")
		assert.Error(t, err)

		r3 := new(mockJobSpecificSearchResolver)
		r3.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32{1}, nil).Once()
		r3.On("ResolveLocations", mock.Anything, false).Return([]int32{11002}, (*address.LocationRequest)(nil), []*address.LocationRequest{}, []*address.LocationRequest{}, nil).Once()
		r3.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), errors.New("dayoff failed")).Once()
		uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, r3, nil, nil)
		_, _, _, err = uc.executeByInput(base, "")
		assert.Error(t, err)

		r4 := new(mockJobSpecificSearchResolver)
		r4.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32{1}, nil).Once()
		r4.On("ResolveLocations", mock.Anything, false).Return([]int32{11002}, (*address.LocationRequest)(nil), []*address.LocationRequest{}, []*address.LocationRequest{}, nil).Once()
		r4.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), nil).Once()
		r4.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(0), errors.New("overtime failed")).Once()
		uc = NewSearchWithJobTypeUseCase(&tmock.MockLogger{}, nil, nil, nil, nil, r4, nil, nil)
		_, _, _, err = uc.executeByInput(base, "")
		assert.Error(t, err)
	})

	t.Run("保存失敗は握りつぶして検索失敗を返す場合", func(t *testing.T) {
		resolver := new(mockJobSpecificSearchResolver)
		resolver.On("ResolveJobTypeSmallIDs", []string{"A"}).Return([]int32{1}, nil).Once()
		resolver.On("ResolveLocations", mock.Anything, false).Return(
			[]int32{11002},
			&address.LocationRequest{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
			[]*address.LocationRequest{},
			[]*address.LocationRequest{},
			nil,
		).Once()
		resolver.On("ResolveDayOffs", (*[]string)(nil)).Return([]int32(nil), nil).Once()
		resolver.On("ResolveAverageOvertime", (*string)(nil)).Return(int32(0), nil).Once()

		profileRepo := new(mockJobSearchFilterRepo)
		profileRepo.On("GetTypedJobSearchFilterBySessionID", "sid").Return((*jobfilter.JobSearchFilter)(nil), errors.New("persist failed")).Once()

		mv := new(mockMvGateway)
		mv.On("GetWillPositionList", mock.Anything, mock.Anything, mock.Anything).Return([]*iface.PositionListEntry{}, errors.New("mv failed")).Once()

		uc := NewSearchWithJobTypeUseCase(
			&tmock.MockLogger{},
			mv,
			nil,
			nil,
			&mockReadPositionRepository{},
			resolver,
			pfilter.NewJobSearchFilterService(&tmock.MockLogger{}, profileRepo),
			pfilter.NewJobSearchFilterService(&tmock.MockLogger{}, profileRepo),
		)
		_, _, _, err := uc.executeByInput(&pcontracts.JobSpecificSearchInput{
			JobTypeLargeID: master.JobTypeLargeIDITSpecialist,
			Salary:         1,
			Locations: []*address.LocationRequest{
				{LocationType: address.LOCATION_TYPE_RESIDENCE, PrefectureName: "北海道", CityName: "札幌市"},
			},
			Custom: &mockJobSpecificParams{
				extensions: []pcontracts.SearchExtension{&mockSearchExtension{remote: false}},
			},
		}, "")
		assert.Error(t, err)
	})
}
