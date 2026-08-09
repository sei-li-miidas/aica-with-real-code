package position

import (
	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	positionUC "aica/api/api/mcptool/usecase/position"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pfilter "aica/api/api/mcptool/usecase/position/filter"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	jobSpecificParams "aica/api/api/mcptool/usecase/position/params"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	positionVectorDomain "aica/api/domain/position"
	"aica/api/domain/public/master"
	"aica/api/domain/search"
	companyDomain "aica/api/domain/user/apply/company"
	positionDomain "aica/api/domain/user/apply/position"
	"aica/api/domain/user/apply/vo"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/logger"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
	"unsafe"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/labstack/echo/v4"
	"github.com/pgvector/pgvector-go"
	"gorm.io/datatypes"
	"gorm.io/gorm"
)

type stubMVGateway struct {
	list []*iface.PositionListEntry
	err  error
}

func (s *stubMVGateway) GetWillPositionList(_ *iface.Company, _ *iface.Business, _ *iface.Position) ([]*iface.PositionListEntry, error) {
	return s.list, s.err
}

type stubPositionRepo struct {
	byID   *positionDomain.Position
	getErr error
	byIDs  positionDomain.Positions
	idsErr error
}

func (s *stubPositionRepo) Get(_ positionDomain.ID) (*positionDomain.Position, error) {
	return s.byID, s.getErr
}

func (s *stubPositionRepo) GetByIDs(_ []positionDomain.ID) (positionDomain.Positions, error) {
	return s.byIDs, s.idsErr
}

type stubCompanyRepo struct {
	company *companyDomain.Company
	err     error
}

func (s *stubCompanyRepo) Get(_ companyDomain.ID) (*companyDomain.Company, error) {
	return s.company, s.err
}

type stubPositionValidator struct {
	err error
}

func (s *stubPositionValidator) ValidatePositionSearchParams(_ *pmodel.GenericPositionSearchParams) error {
	return s.err
}

type stubLocationLookup struct {
	commutingIDs []int
	workCityIDs  []int
	err          error
}

func (s *stubLocationLookup) GetCommutingAreasFromResidence(_ string, _ string) ([]int, error) {
	if s.err != nil {
		return nil, s.err
	}
	return s.commutingIDs, nil
}

func (s *stubLocationLookup) GetCityIDsFromWorkLocations(_ []struct{ PrefectureName, CityName string }) ([]int, error) {
	if s.err != nil {
		return nil, s.err
	}
	return s.workCityIDs, nil
}

type stubJobTypeSearchToolResolver struct {
	toolNameByJobtype map[string]string
	jobtypesByTool    map[string][]string
}

func (s *stubJobTypeSearchToolResolver) ToolNameByJobtypeName(name string) string {
	if s == nil {
		return ""
	}
	return s.toolNameByJobtype[name]
}

func (s *stubJobTypeSearchToolResolver) JobtypeNamesByToolName(toolName string) []string {
	if s == nil {
		return nil
	}
	names := s.jobtypesByTool[toolName]
	if len(names) == 0 {
		return nil
	}
	return append([]string{}, names...)
}

func newStubJobTypeSearchToolResolver() pinterfaces.JobTypeSearchToolResolver {
	return &stubJobTypeSearchToolResolver{
		toolNameByJobtype: map[string]string{
			"ITコンサルタント（アプリ）": pcontracts.ToolNameSearchJobPostingsForITEngineer,
			"Webアプリ開発":       pcontracts.ToolNameSearchJobPostingsForITEngineer,
			"金融営業（法人）":       pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
			"金融営業（個人）":       pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
		},
		jobtypesByTool: map[string][]string{
			pcontracts.ToolNameSearchJobPostingsForITEngineer: {
				"ITコンサルタント（アプリ）",
				"Webアプリ開発",
			},
			pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales: {
				"金融営業（法人）",
				"金融営業（個人）",
			},
		},
	}
}

type stubJobSpecificResolver struct {
	jobTypeSmallIDs []int32
	jobTypeErr      error
	cityIDs         []int32
	commutingIDs    []int32
	residence       *address.LocationRequest
	workLocations   []*address.LocationRequest
	locationErr     error
	skills          master.Skills
	skillsErr       error
	dayOffs         []int32
	dayOffsErr      error
	avgOvertime     int32
	avgOvertimeErr  error
	salesStyleDive  int32
	salesStyleErr   error
}

func (s *stubJobSpecificResolver) ExistsPrefectureCity(_ string, _ string) bool {
	return true
}

func (s *stubJobSpecificResolver) ResolveJobTypeSmallIDs(_ []string) ([]int32, error) {
	if s.jobTypeSmallIDs == nil {
		return []int32{1}, s.jobTypeErr
	}
	return s.jobTypeSmallIDs, s.jobTypeErr
}
func (s *stubJobSpecificResolver) ResolveLocations(_ []*address.LocationRequest, _ bool) ([]int32, *address.LocationRequest, []*address.LocationRequest, []*address.LocationRequest, error) {
	commuting := make([]*address.LocationRequest, 0, len(s.commutingIDs))
	for _, id := range s.commutingIDs {
		if id == 0 {
			continue
		}
		commuting = append(commuting, &address.LocationRequest{LocationType: address.LOCATION_TYPE_COMMUTING_AREAS, PrefectureName: "東京都", CityName: "新宿区"})
	}
	return s.cityIDs, s.residence, commuting, s.workLocations, s.locationErr
}
func (s *stubJobSpecificResolver) ResolveLocationByName(name string) (*address.LocationRequest, error) {
	return &address.LocationRequest{PrefectureName: "東京都", CityName: "新宿区"}, nil
}
func (s *stubJobSpecificResolver) ResolveSkills(_ []string) (master.Skills, error) {
	if s.skills == nil {
		return master.Skills{&master.Skill{ID: 1}}, s.skillsErr
	}
	return s.skills, s.skillsErr
}
func (s *stubJobSpecificResolver) ResolveDayOffs(_ *[]string) ([]int32, error) {
	if s.dayOffs == nil {
		return []int32{1}, s.dayOffsErr
	}
	return s.dayOffs, s.dayOffsErr
}
func (s *stubJobSpecificResolver) ResolveAverageOvertime(_ *string) (int32, error) {
	if s.avgOvertime == 0 {
		return 1, s.avgOvertimeErr
	}
	return s.avgOvertime, s.avgOvertimeErr
}
func (s *stubJobSpecificResolver) ResolveSalesStyleDive(_ *string) (int32, error) {
	if s.salesStyleDive == 0 {
		return 1, s.salesStyleErr
	}
	return s.salesStyleDive, s.salesStyleErr
}

type stubJobSearchFilterRepo struct {
	current     *jobfilter.JobSearchFilter
	reloaded    *jobfilter.JobSearchFilter
	getErr      error
	upsertErr   error
	lastSession string
	lastJSON    datatypes.JSON
	getCalls    int
}

func (s *stubJobSearchFilterRepo) GetTypedJobSearchFilterBySessionID(_ string) (*jobfilter.JobSearchFilter, error) {
	if s.getErr != nil {
		return nil, s.getErr
	}
	s.getCalls++
	if s.reloaded != nil && s.getCalls > 1 {
		return s.reloaded, nil
	}
	return s.current, nil
}
func (s *stubJobSearchFilterRepo) GetJobSearchFilterBySessionID(_ string) (*datatypes.JSON, error) {
	return nil, s.getErr
}
func (s *stubJobSearchFilterRepo) UpsertJobSearchFilter(sessionID string, payload datatypes.JSON) error {
	s.lastSession = sessionID
	s.lastJSON = payload
	if s.upsertErr != nil {
		return s.upsertErr
	}
	var persisted jobfilter.JobSearchFilter
	if err := json.Unmarshal(payload, &persisted); err == nil {
		s.current = &persisted
	}
	return nil
}

type stubVectorizerRepo struct {
	embeddingErr error
}

func (s *stubVectorizerRepo) GenerateEmbedding(_ string) (*pgvector.Vector, error) {
	if s.embeddingErr != nil {
		return nil, s.embeddingErr
	}
	v := pgvector.NewVector([]float32{0.1, 0.2, 0.3})
	return &v, nil
}
func (s *stubVectorizerRepo) GenerateEmbeddings(_ []*vectorizer.EmbeddingTarget) ([]*vectorizer.EmbeddingResult, error) {
	return nil, nil
}

type stubPositionVectorRepo struct {
	results []*positionVectorDomain.PositionSearchResult
	err     error
}

func (s *stubPositionVectorRepo) SemanticSearch(_ string, _ float64, _ func(*gorm.DB) *gorm.DB) ([]*positionVectorDomain.PositionSearchResult, error) {
	return s.results, s.err
}

var (
	_ pinterfaces.PositionGetter                                                  = (*stubPositionRepo)(nil)
	_ pinterfaces.PositionSearchValidator                                         = (*stubPositionValidator)(nil)
	_ pinterfaces.LocationLookup                                                  = (*stubLocationLookup)(nil)
	_ pcontracts.JobSpecificSearchResolver                                        = (*stubJobSpecificResolver)(nil)
	_ pinterfaces.JobSearchFilterRepository                                       = (*stubJobSearchFilterRepo)(nil)
	_ vectorizer.VectorizerRepository                                             = (*stubVectorizerRepo)(nil)
	_ search.SemanticSearchRepository[*positionVectorDomain.PositionSearchResult] = (*stubPositionVectorRepo)(nil)
)

func TestPositionAPIs_SuccessPathsWithCustomHandlerFactories(t *testing.T) {
	log := &tmock.MockLogger{}
	setMasterCacheForRouteAPITest(&master.Cache{
		PrefectureCities:           master.PrefectureCities{{PrefectureName: "東京都", CityName: "23区", RealCityName: "新宿区", CityID: 139999}},
		TraitPositionOptions:       map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
		TraitBusinessOptions:       map[master.MasterTraitBusinessID][]*master.TraitBusinessOption{},
		TraitCompanyOptions:        map[master.MasterTraitCompanyID][]*master.TraitCompanyOption{},
		Skills:                     master.Skills{},
		SkillGroups:                master.SkillGroups{},
		JobTypeSmalls:              master.JobTypeSmalls{&master.JobTypeSmall{ID: 1, Name: "リアル職種SE"}},
		SpotJobRequests:            master.SpotJobRequests{},
		SpotExpLevels:              master.SpotExpLevels{},
		Interviewers:               []*master.Interviewer{},
		WorkExperiencePatterns:     []*master.WorkExperiencePattern{},
		WorkExperienceTimings:      []*master.WorkExperienceTiming{},
		WorkExperienceContentTypes: []*master.WorkExperienceContentType{},
		WorkExperienceTimeframes:   []*master.WorkExperienceTimeframe{},
		WorkExperienceNeedtimes:    []*master.WorkExperienceNeedtime{},
		WorkExperienceRewards:      []*master.WorkExperienceReward{},
	})
	mv := &stubMVGateway{
		list: []*iface.PositionListEntry{{PositionId: 1}},
	}
	repo := &stubPositionRepo{
		byID: &positionDomain.Position{
			ID:        1,
			CompanyID: 1,
			Detail: positionDomain.Detail{
				Title:          "detail title",
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDEmployee)},
				GuaranteedIncome: &positionDomain.GuaranteedIncome{
					BulkIncomeFrom: func() *int { v := 500; return &v }(),
					BulkIncomeTo:   func() *int { v := 700; return &v }(),
				},
			},
		},
		byIDs: positionDomain.Positions{
			{ID: 1, Detail: positionDomain.Detail{Title: "summary title", MainJobText: "summary text"}},
		},
	}
	companyRepo := &stubCompanyRepo{
		company: &companyDomain.Company{ID: 1, Detail: companyDomain.Detail{Name: "company"}},
	}

	jobSpecificParams.ITEngineerSearchFilters = []*jobfilter.JobSearchFilterOtherFilter{
		{Name: "言語（all）", Type: jobfilter.JobSearchFilterTypeMultiple, Options: []*jobfilter.JobSearchFilterOtherFilterOption{{Label: "Go"}}},
	}
	jobSpecificParams.FinancialSalesSearchFilters = []*jobfilter.JobSearchFilterOtherFilter{
		{Name: "取扱商材（金融商品）", Type: jobfilter.JobSearchFilterTypeMultiple, Options: []*jobfilter.JobSearchFilterOtherFilterOption{{Label: "保険"}}},
	}
	genericFilterRepo := &stubJobSearchFilterRepo{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostings: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
						JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "SE", Value: "SE"},
						Selected:                         true,
					}},
				},
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{
						JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "ITコンサルタント（アプリ）", Value: "ITコンサルタント（アプリ）"},
						Selected:                         false,
					}},
				},
			},
			Locations: &jobfilter.JobSearchFilterLocations{
				WorkLocations:      []*jobfilter.JobSearchFilterLocationSelectableItem{},
				RemoteWorkPossible: func() *bool { v := true; return &v }(),
			},
			Salary: 600,
			SelectedOtherFilterOptions: map[string]map[string][]string{
				pcontracts.SelectedFilterOptionsCommonKey: {},
			},
		},
	}
	genericFilterService := pfilter.NewJobSearchFilterService(log, genericFilterRepo)

	handler := NewHandler(HandlerDependencies{
		NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
			return positionUC.NewGenericSearchUseCase(
				l,
				mv,
				nil,
				nil,
				repo,
				&stubPositionValidator{},
				&stubLocationLookup{},
			)
		},
		NewJobTypeSmallIDResolver: func(_ logger.LevelLogger) pcontracts.JobSpecificSearchResolver {
			return &stubJobSpecificResolver{}
		},
		NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
			return positionUC.NewDetailUseCase(repo, companyRepo, master.Provider(), l)
		},
		NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
			return positionUC.NewSummariesUseCase(l, repo)
		},
		NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, enablePersistence bool) (SearchWithJobTypeUseCase, error) {
			_ = enablePersistence
			fs := pfilter.NewJobSearchFilterService(l, &stubJobSearchFilterRepo{
				current: &jobfilter.JobSearchFilter{
					Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
						pcontracts.ToolNameSearchJobPostingsForITEngineer: {
							{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "SE", Value: "SE"}, Selected: true}},
						},
						pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales: {
							{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "SE", Value: "SE"}, Selected: true}},
						},
					},
					Locations: &jobfilter.JobSearchFilterLocations{
						Residence: &jobfilter.JobSearchFilterResidence{
							Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
						},
					},
					Salary: 600,
				},
			})
			return positionUC.NewSearchWithJobTypeUseCase(
				l,
				mv,
				nil,
				nil,
				repo,
				&stubJobSpecificResolver{},
				fs,
				fs,
			), nil
		},
		NewGenericSearchFilterPersister: func(_ logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister {
			return genericFilterService
		},
		NewJobSearchFilterReader: func(_ logger.LevelLogger) pinterfaces.JobSearchFilterReader {
			return genericFilterService
		},
		JobTypeSearchToolResolver: newStubJobTypeSearchToolResolver(),
	})
	module := &Module{handler: handler}
	e, err := newMockBootstrapServer(log, module)
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	t.Run("汎用検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequestWithHeader(e, http.MethodPost, "/positions/search", `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"フルリモート"}]}`, "session-generic-response")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
		var body map[string]any
		if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
			t.Fatalf("failed to decode response: %v", err)
		}
		searchFilters, ok := body["SearchFilters"].(map[string]any)
		if !ok {
			t.Fatalf("expected SearchFilters in response")
		}
		jobtypes, ok := searchFilters["Jobtypes"].(map[string]any)
		if !ok {
			t.Fatalf("expected Jobtypes in SearchFilters: %+v", searchFilters)
		}
		if _, ok := jobtypes[pcontracts.ToolNameSearchJobPostings].([]any); !ok {
			t.Fatalf("expected generic jobtype group in SearchFilters: %+v", jobtypes)
		}
		if _, ok := jobtypes[pcontracts.ToolNameSearchJobPostingsForITEngineer].([]any); !ok {
			t.Fatalf("expected persisted IT jobtype group in SearchFilters: %+v", jobtypes)
		}
		if _, ok := searchFilters["Locations"].(map[string]any); !ok {
			t.Fatalf("expected Locations in SearchFilters: %+v", searchFilters)
		}
		if salary, ok := searchFilters["Salary"].(float64); !ok || int(salary) != 600 {
			t.Fatalf("expected Salary=600 in SearchFilters: %+v", searchFilters)
		}
		otherFilters, ok := searchFilters["OtherFilters"].(map[string]any)
		if !ok {
			t.Fatalf("expected grouped OtherFilters in SearchFilters: %+v", searchFilters)
		}
		if _, ok := otherFilters[pcontracts.ToolNameSearchJobPostingsForITEngineer].([]any); !ok {
			t.Fatalf("expected persisted IT other filters in SearchFilters: %+v", otherFilters)
		}
		if _, exists := otherFilters[pcontracts.ToolNameSearchJobPostings]; exists {
			t.Fatalf("did not expect generic OtherFilters group: %+v", otherFilters)
		}
	})

	t.Run("汎用検索でフルリモートを含むフィルタを保存できる", func(t *testing.T) {
		rec := performJSONRequestWithHeader(e, http.MethodPost, "/positions/search", `{
			"Salary":600,
			"JobtypeNames":["SE","ITコンサルタント（アプリ）"],
			"Locations":[{"LocationType":"フルリモート"}]
		}`, "session-generic")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
		if genericFilterRepo.lastSession != "session-generic" || len(genericFilterRepo.lastJSON) == 0 {
			t.Fatalf("expected persisted filter for generic search")
		}
		var persisted jobfilter.JobSearchFilter
		if err := json.Unmarshal(genericFilterRepo.lastJSON, &persisted); err != nil {
			t.Fatalf("failed to decode persisted filter: %v", err)
		}
		group := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostings]
		if len(group) != 2 {
			t.Fatalf("expected persisted jobtypes to keep known options, got %+v", persisted.Jobtypes)
		}
		if group[0].Value != "SE" || !group[0].Selected {
			t.Fatalf("expected explicitly requested jobtype SE to remain selected, got %+v", group[0])
		}
		if group[1].Value != "ITコンサルタント（アプリ）" || !group[1].Selected {
			t.Fatalf("expected requested jobtype selected without semantic expansion, got %+v", group[1])
		}
		if len(persisted.Locations.WorkLocations) != 0 {
			t.Fatalf("expected no work locations in persisted filter, got %+v", persisted.Locations.WorkLocations)
		}
		if persisted.Locations.RemoteWorkPossible == nil || !*persisted.Locations.RemoteWorkPossible {
			t.Fatalf("expected remote work possible to be true in persisted filter, got %+v", persisted.Locations.RemoteWorkPossible)
		}
	})

	t.Run("ツール名に応じてITエンジニア経路へ分岐する", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search", `{
			"ToolName":"search_job_postings_for_it_engineer",
			"Salary":600,
			"JobtypeNames":["SE"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
			"ProgrammingLanguages":["Go"]
		}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
		var body map[string]any
		if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
			t.Fatalf("invalid response json: %v", err)
		}
		searchFilters, ok := body["SearchFilters"]
		if !ok || searchFilters == nil {
			t.Fatalf("expected SearchFilters in response")
		}
		jobtypeNames, ok := body["JobtypeNamesWithSameSearchFilters"].(map[string]any)
		if !ok || len(jobtypeNames) == 0 {
			t.Fatalf("expected JobtypeNamesWithSameSearchFilters to be populated")
		}
	})

	t.Run("ツール名に応じて金融営業経路へ分岐する", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search", `{
			"ToolName":"search_job_postings_for_sales_financial_sales",
			"Salary":600,
			"JobtypeNames":["FS"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
			"HandledFinancialProducts":["保険"]
		}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
		var body map[string]any
		if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
			t.Fatalf("invalid response json: %v", err)
		}
		searchFilters, ok := body["SearchFilters"]
		if !ok || searchFilters == nil {
			t.Fatalf("expected SearchFilters in response")
		}
		jobtypeNames, ok := body["JobtypeNamesWithSameSearchFilters"].(map[string]any)
		if !ok || len(jobtypeNames) == 0 {
			t.Fatalf("expected JobtypeNamesWithSameSearchFilters to be populated")
		}
	})

	t.Run("レコメンド検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/recommendations/theme1", ``, "session-generic")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("ITエンジニア検索で保存も含めて成功する場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("IT向け職種別検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/jobtype_specific", `{"Salary":600,"JobtypeNames":["ITコンサルタント（アプリ）"],"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("ITエンジニアのテーマ検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/recommendations/it_engineer/theme1", ``, "session-it-theme")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("汎用レコメンドの全テーマ検索が成功する場合", func(t *testing.T) {
		themes := []string{"theme1", "theme2", "theme3", "theme4", "theme5", "theme6", "theme7", "theme8", "theme9"}
		for _, theme := range themes {
			rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/recommendations/"+theme, ``, "session-generic")
			if rec.Code != http.StatusOK {
				t.Fatalf("theme=%s expected 200 got %d body=%s", theme, rec.Code, rec.Body.String())
			}
		}
	})

	t.Run("ITの全テーマ検索が成功する場合", func(t *testing.T) {
		themes := []string{"theme1", "theme2", "theme3", "theme4", "theme5", "theme6", "theme7", "theme8", "theme9"}
		for _, theme := range themes {
			rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/recommendations/it_engineer/"+theme, ``, "session-it-theme")
			if rec.Code != http.StatusOK {
				t.Fatalf("theme=%s expected 200 got %d body=%s", theme, rec.Code, rec.Body.String())
			}
		}
	})

	t.Run("金融営業検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/financial_sales", `{
			"Salary":600,
			"JobtypeNames":["FS"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]
		}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("金融営業向け職種別検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/jobtype_specific", `{
			"Salary":600,
			"JobtypeNames":["金融営業（法人）"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]
		}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("金融営業のテーマ検索が成功する場合", func(t *testing.T) {
		rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/recommendations/financial_sales/theme1", ``, "session-fin-theme")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("金融営業の全テーマ検索が成功する場合", func(t *testing.T) {
		themes := []string{"theme1", "theme2", "theme3", "theme4", "theme5", "theme6", "theme7", "theme8", "theme9"}
		for _, theme := range themes {
			rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/recommendations/financial_sales/"+theme, ``, "session-fin-theme")
			if rec.Code != http.StatusOK {
				t.Fatalf("theme=%s expected 200 got %d body=%s", theme, rec.Code, rec.Body.String())
			}
		}
	})

	t.Run("詳細取得が成功する場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/detail/1", `{}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})
}

func TestPositionAPIs_ErrorPathsWithCustomFactories(t *testing.T) {
	log := &tmock.MockLogger{}
	mv := &stubMVGateway{err: errors.New("mv failed")}
	repo := &stubPositionRepo{
		getErr: errors.New("repo get failed"),
		idsErr: errors.New("repo ids failed"),
	}
	handler := NewHandler(HandlerDependencies{
		NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
			return positionUC.NewGenericSearchUseCase(
				l, mv, nil, nil, repo,
				&stubPositionValidator{err: nil},
				&stubLocationLookup{},
			)
		},
		NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
			return positionUC.NewDetailUseCase(repo, &stubCompanyRepo{}, master.Provider(), l)
		},
		NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
			return positionUC.NewSummariesUseCase(l, repo)
		},
		NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
			return positionUC.NewSearchWithJobTypeUseCase(
				l, mv, nil, nil, repo, &stubJobSpecificResolver{}, nil, nil,
			), nil
		},
	})
	module := &Module{handler: handler}
	e, err := newMockBootstrapServer(log, module)
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	rec := performJSONRequest(e, "/positions/search", `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"フルリモート"}]}`)
	if rec.Code < http.StatusBadRequest {
		t.Fatalf("expected error response for mv error, got %d", rec.Code)
	}

	rec = performJSONRequest(e, "/positions/summaries", `{"PositionIDs":[1]}`)
	if rec.Code < http.StatusBadRequest {
		t.Fatalf("expected error response for summaries repo error, got %d", rec.Code)
	}

	rec = performJSONRequest(e, "/positions/detail/1", `{}`)
	if rec.Code < http.StatusBadRequest {
		t.Fatalf("expected error response for detail repo error, got %d", rec.Code)
	}
}

func TestPositionAPIs_GenericSearch_ResolverAndSemanticBranches(t *testing.T) {
	log := &tmock.MockLogger{}
	baseMV := &stubMVGateway{list: []*iface.PositionListEntry{{PositionId: 1}}}
	repo := &stubPositionRepo{
		byIDs: positionDomain.Positions{
			{ID: 1, Detail: positionDomain.Detail{Title: "summary title", MainJobText: "summary text"}},
		},
	}

	tests := []struct {
		name          string
		validator     *stubPositionValidator
		location      *stubLocationLookup
		jobTypeErr    error
		vectorizer    *stubVectorizerRepo
		positionVec   *stubPositionVectorRepo
		body          string
		expectedError bool
	}{
		{
			name:          "validator error",
			validator:     &stubPositionValidator{err: errors.New("invalid params")},
			location:      &stubLocationLookup{},
			body:          `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"フルリモート"}]}`,
			expectedError: true,
		},
		{
			name:          "location resolver error",
			validator:     &stubPositionValidator{},
			location:      &stubLocationLookup{err: errors.New("location failed")},
			body:          `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]}`,
			expectedError: true,
		},
		{
			name:          "jobtype resolver error",
			validator:     &stubPositionValidator{},
			location:      &stubLocationLookup{},
			jobTypeErr:    errors.New("jobtype failed"),
			body:          `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"フルリモート"}]}`,
			expectedError: true,
		},
		{
			name:        "semantic success",
			validator:   &stubPositionValidator{},
			location:    &stubLocationLookup{},
			vectorizer:  &stubVectorizerRepo{},
			positionVec: &stubPositionVectorRepo{results: []*positionVectorDomain.PositionSearchResult{{ID: 1, Distance: 0.1}}},
			body:        `{"Salary":600,"JobtypeNames":["SE"],"PositionKeyword":"go","Locations":[{"LocationType":"フルリモート"}]}`,
		},
		{
			name:          "semantic embedding error",
			validator:     &stubPositionValidator{},
			location:      &stubLocationLookup{},
			vectorizer:    &stubVectorizerRepo{embeddingErr: errors.New("embed failed")},
			positionVec:   &stubPositionVectorRepo{},
			body:          `{"Salary":600,"JobtypeNames":["SE"],"PositionKeyword":"go","Locations":[{"LocationType":"フルリモート"}]}`,
			expectedError: true,
		},
		{
			name:          "semantic repository error",
			validator:     &stubPositionValidator{},
			location:      &stubLocationLookup{},
			vectorizer:    &stubVectorizerRepo{},
			positionVec:   &stubPositionVectorRepo{err: errors.New("semantic failed")},
			body:          `{"Salary":600,"JobtypeNames":["SE"],"PositionKeyword":"go","Locations":[{"LocationType":"フルリモート"}]}`,
			expectedError: true,
		},
	}

	runCase := func(tc struct {
		name          string
		validator     *stubPositionValidator
		location      *stubLocationLookup
		jobTypeErr    error
		vectorizer    *stubVectorizerRepo
		positionVec   *stubPositionVectorRepo
		body          string
		expectedError bool
	}) {
		t.Run(tc.name, func(t *testing.T) {
			handler := NewHandler(HandlerDependencies{
				NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
					return positionUC.NewGenericSearchUseCase(l, baseMV, tc.vectorizer, tc.positionVec, repo, tc.validator, tc.location)
				},
				NewJobTypeSmallIDResolver: func(_ logger.LevelLogger) pcontracts.JobSpecificSearchResolver {
					return &stubJobSpecificResolver{jobTypeErr: tc.jobTypeErr}
				},
				NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
					return positionUC.NewDetailUseCase(repo, &stubCompanyRepo{}, master.Provider(), l)
				},
				NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
					return positionUC.NewSummariesUseCase(l, repo)
				},
				NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
					return positionUC.NewSearchWithJobTypeUseCase(l, baseMV, nil, nil, repo, &stubJobSpecificResolver{}, nil, nil), nil
				},
			})
			e, err := newMockBootstrapServer(log, &Module{handler: handler})
			if err != nil {
				t.Fatalf("setup failed: %v", err)
			}

			rec := performJSONRequest(e, "/positions/search", tc.body)
			if tc.expectedError && rec.Code < http.StatusBadRequest {
				t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
			}
			if !tc.expectedError && rec.Code != http.StatusOK {
				t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
			}
		})
	}

	runCase(tests[0])
	runCase(tests[1])
	runCase(tests[2])
	runCase(tests[3])
	runCase(tests[4])
	runCase(tests[5])

	t.Run("バリデータが未設定の場合", func(t *testing.T) {
		handler := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				return positionUC.NewGenericSearchUseCase(l, baseMV, nil, nil, repo, nil, &stubLocationLookup{})
			},
			NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
				return positionUC.NewDetailUseCase(repo, &stubCompanyRepo{}, master.Provider(), l)
			},
			NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
				return positionUC.NewSummariesUseCase(l, repo)
			},
			NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				return positionUC.NewSearchWithJobTypeUseCase(l, baseMV, nil, nil, repo, &stubJobSpecificResolver{}, nil, nil), nil
			},
		})
		e, _ := newMockBootstrapServer(log, &Module{handler: handler})
		rec := performJSONRequest(e, "/positions/search", `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"フルリモート"}]}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("リゾルバ群が未設定の場合", func(t *testing.T) {
		handler := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				return positionUC.NewGenericSearchUseCase(l, baseMV, nil, nil, repo, &stubPositionValidator{}, nil)
			},
			NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
				return positionUC.NewDetailUseCase(repo, &stubCompanyRepo{}, master.Provider(), l)
			},
			NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
				return positionUC.NewSummariesUseCase(l, repo)
			},
			NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				return positionUC.NewSearchWithJobTypeUseCase(l, baseMV, nil, nil, repo, &stubJobSpecificResolver{}, nil, nil), nil
			},
		})
		e, _ := newMockBootstrapServer(log, &Module{handler: handler})
		rec := performJSONRequest(e, "/positions/search", `{"Salary":600,"JobtypeNames":["SE"],"Locations":[{"LocationType":"フルリモート"}]}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})
}

func TestPositionAPIs_JobSpecificResolverAndPersistenceBranches(t *testing.T) {
	log := &tmock.MockLogger{}
	setMasterCacheForRouteAPITest(&master.Cache{
		PrefectureCities:     master.PrefectureCities{{PrefectureName: "東京都", CityName: "23区", RealCityName: "新宿区", CityID: 139999}},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{},
		Skills:               master.Skills{},
		SkillGroups:          master.SkillGroups{},
	})

	jobSpecificParams.ITEngineerSearchFilters = []*jobfilter.JobSearchFilterOtherFilter{
		{Name: "言語（all）", Type: jobfilter.JobSearchFilterTypeMultiple, Options: []*jobfilter.JobSearchFilterOtherFilterOption{{Label: "Go"}, {Label: "Ruby"}}},
	}
	jobSpecificParams.FinancialSalesSearchFilters = []*jobfilter.JobSearchFilterOtherFilter{
		{Name: "取扱商材（金融商品）", Type: jobfilter.JobSearchFilterTypeMultiple, Options: []*jobfilter.JobSearchFilterOtherFilterOption{{Label: "保険"}}},
	}

	baseMV := &stubMVGateway{list: []*iface.PositionListEntry{{PositionId: 1}}}
	repo := &stubPositionRepo{
		byIDs: positionDomain.Positions{
			{ID: 1, Detail: positionDomain.Detail{Title: "summary title", MainJobText: "summary text"}},
		},
	}
	filterRepo := &stubJobSearchFilterRepo{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "既存職種", Value: "既存職種"}}},
				},
			},
			Locations: &jobfilter.JobSearchFilterLocations{
				Residence: &jobfilter.JobSearchFilterResidence{
					Address:        &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
					CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{{Label: "東京都新宿区", PrefectureName: "東京都", CityName: "新宿区"}},
				},
				WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{{Label: "東京都新宿区", PrefectureName: "東京都", CityName: "新宿区"}},
			},
		},
	}

	newHandler := func(resolver *stubJobSpecificResolver, filter *stubJobSearchFilterRepo) *Handler {
		return NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				return positionUC.NewGenericSearchUseCase(l, baseMV, nil, nil, repo, &stubPositionValidator{}, &stubLocationLookup{})
			},
			NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
				return positionUC.NewDetailUseCase(repo, &stubCompanyRepo{}, master.Provider(), l)
			},
			NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
				return positionUC.NewSummariesUseCase(l, repo)
			},
			NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, enablePersistence bool) (SearchWithJobTypeUseCase, error) {
				var fs *pfilter.JobSearchFilterService
				if enablePersistence {
					fs = pfilter.NewJobSearchFilterService(l, filter)
				}
				return positionUC.NewSearchWithJobTypeUseCase(l, baseMV, nil, nil, repo, resolver, fs, fs), nil
			},
		})
	}

	t.Run("IT検索で選択フィルタを保存して返せる", func(t *testing.T) {
		filterRepo.reloaded = &jobfilter.JobSearchFilter{
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
			Locations: &jobfilter.JobSearchFilterLocations{
				Residence: &jobfilter.JobSearchFilterResidence{
					Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
				},
			},
			Salary: 600,
			SelectedOtherFilterOptions: map[string]map[string][]string{
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					"言語（all）": {"Go"},
				},
			},
		}
		filterRepo.getCalls = 0
		e, err := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{}, filterRepo)})
		if err != nil {
			t.Fatalf("setup failed: %v", err)
		}
		rec := performJSONRequestWithHeader(e, http.MethodPost, "/positions/search/it_engineer", `{
			"Salary":600,
			"JobtypeNames":["SE"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
			"ProgrammingLanguages":["Go"]
		}`, "session-1")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
		if filterRepo.lastSession != "session-1" || len(filterRepo.lastJSON) == 0 {
			t.Fatalf("expected filter persistence with session")
		}
		var body map[string]any
		if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
			t.Fatalf("invalid response json: %v", err)
		}
		searchFilters, ok := body["SearchFilters"].(map[string]any)
		if !ok {
			t.Fatalf("expected SearchFilters in response")
		}
		jobtypes, ok := searchFilters["Jobtypes"].(map[string]any)
		if !ok {
			t.Fatalf("expected Jobtypes in SearchFilters: %+v", searchFilters)
		}
		group, ok := jobtypes[pcontracts.ToolNameSearchJobPostingsForITEngineer].([]any)
		if !ok || len(group) != 1 {
			t.Fatalf("expected IT jobtype group in response: %+v", jobtypes)
		}
		first, ok := group[0].(map[string]any)
		if !ok {
			t.Fatalf("expected jobtype item object: %+v", group[0])
		}
		if desc, ok := first["Description"].(string); !ok || strings.TrimSpace(desc) == "" {
			t.Fatalf("expected non-empty Description in response: %+v", first)
		}
	})

	t.Run("金融営業検索で勤務地を保存できる", func(t *testing.T) {
		e, err := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{}, filterRepo)})
		if err != nil {
			t.Fatalf("setup failed: %v", err)
		}
		rec := performJSONRequestWithHeader(e, http.MethodPost, "/positions/search/financial_sales", `{
			"Salary":600,
			"JobtypeNames":["FS"],
			"Locations":[
				{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"},
				{"LocationType":"希望勤務地","PrefectureName":"東京都","CityName":"新宿区"}
			]
		}`, "session-fin")
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
		if filterRepo.lastSession != "session-fin" || len(filterRepo.lastJSON) == 0 {
			t.Fatalf("expected persisted filter for financial search")
		}
	})

	t.Run("職種リゾルバがエラーを返す場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{jobTypeErr: errors.New("jobtype failed")}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{"Salary":600,"JobtypeNames":["SE"],"RemoteWork":"条件なし"}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("勤務地リゾルバがエラーを返す場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{locationErr: errors.New("location failed")}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{
			"Salary":600,
			"JobtypeNames":["SE"],
			"RemoteWork":"",
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("休日リゾルバがエラーを返す場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{dayOffsErr: errors.New("dayoffs failed")}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{
			"Salary":600,
			"JobtypeNames":["SE"],
			"RemoteWork":"条件なし",
			"DayOffs":["invalid"]
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("平均残業時間リゾルバがエラーを返す場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{avgOvertimeErr: errors.New("ot failed")}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{
			"Salary":600,
			"JobtypeNames":["SE"],
			"RemoteWork":"条件なし",
			"AverageOvertime":"invalid"
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("スキルリゾルバがエラーを返す場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{skillsErr: errors.New("skill failed")}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{
			"Salary":600,
			"JobtypeNames":["SE"],
			"RemoteWork":"条件なし",
			"ProgrammingLanguages":["Go"]
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("営業スタイルリゾルバがエラーを返す場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{salesStyleErr: errors.New("sales style failed")}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/financial_sales", `{
			"Salary":600,
			"JobtypeNames":["FS"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
			"SalesStyleDive":"あり"
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d", rec.Code)
		}
	})

	t.Run("職種別検索で不正な勤務地種別の場合", func(t *testing.T) {
		e, _ := newMockBootstrapServer(log, &Module{handler: newHandler(&stubJobSpecificResolver{}, filterRepo)})
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{
			"Salary":600,
			"JobtypeNames":["SE"],
			"Locations":[{"LocationType":"フルリモート"}],
			"RemoteWork":""
		}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}
	})
}

func TestPositionAPIs_JobTypesSelected_MergesJobtypes(t *testing.T) {
	log := &tmock.MockLogger{}
	filterRepo := &stubJobSearchFilterRepo{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostings: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "A", Value: "A"}, Selected: true}},
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "C", Value: "C"}, Selected: false}},
				},
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "ITコンサルタント（アプリ）", Value: "ITコンサルタント（アプリ）"}, Selected: false}},
				},
			},
			Salary: 500,
		},
	}

	handler := NewHandler(HandlerDependencies{
		NewJobTypesSelectedUseCase: func(l logger.LevelLogger) JobTypesSelectedUseCase {
			return positionUC.NewJobTypesSelectedUseCase(
				l,
				pfilter.NewJobSearchFilterService(l, filterRepo),
				&stubJobSpecificResolver{},
				newStubJobTypeSearchToolResolver(),
			)
		},
	})

	e, err := newMockBootstrapServer(log, &Module{handler: handler})
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	rec := performJSONRequestWithHeader(e, http.MethodPost, "/positions/jobtypes/decided", `{
		"JobtypeNames":["A","B"]
	}`, "session-jt")
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
	}
	var selectionResp struct {
		ToolName string `json:"ToolName"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &selectionResp); err != nil {
		t.Fatalf("failed to decode response: %v", err)
	}
	if selectionResp.ToolName != pcontracts.ToolNameSearchJobPostings {
		t.Fatalf("expected ToolName=%s, got %s", pcontracts.ToolNameSearchJobPostings, selectionResp.ToolName)
	}

	var persisted jobfilter.JobSearchFilter
	if err := json.Unmarshal(filterRepo.lastJSON, &persisted); err != nil {
		t.Fatalf("failed to unmarshal persisted payload: %v", err)
	}
	if filterRepo.lastSession != "session-jt" {
		t.Fatalf("expected session-jt, got %s", filterRepo.lastSession)
	}
	group := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostings]
	if len(group) != 3 {
		t.Fatalf("expected 3 jobtypes after merge, got %d", len(group))
	}
	if group[0].Value != "A" || !group[0].Selected {
		t.Fatalf("expected first jobtype A selected, got %+v", group[0])
	}
	if group[1].Value != "C" || group[1].Selected {
		t.Fatalf("expected second jobtype C kept and unselected, got %+v", group[1])
	}
	if group[2].Value != "B" || !group[2].Selected {
		t.Fatalf("expected third jobtype B appended and selected, got %+v", group[2])
	}
	itGroup := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostingsForITEngineer]
	if len(itGroup) != 1 || itGroup[0].Value != "ITコンサルタント（アプリ）" || itGroup[0].Selected {
		t.Fatalf("expected unrelated IT group to be unselected, got %+v", itGroup)
	}
	if persisted.Salary != 500 {
		t.Fatalf("expected other fields to be kept, salary=%d", persisted.Salary)
	}
}

func TestPositionAPIs_JobTypesClear_ClearsSelection(t *testing.T) {
	log := &tmock.MockLogger{}
	filterRepo := &stubJobSearchFilterRepo{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostings: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "A", Value: "A"}, Selected: true}},
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "B", Value: "B"}, Selected: false}},
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "C", Value: "C"}, Selected: true}},
				},
			},
			Salary: 500,
		},
	}

	handler := NewHandler(HandlerDependencies{
		NewJobSearchFilterReader: func(l logger.LevelLogger) pinterfaces.JobSearchFilterReader {
			return pfilter.NewJobSearchFilterService(l, filterRepo)
		},
		NewJobTypesSelectedUseCase: func(l logger.LevelLogger) JobTypesSelectedUseCase {
			return positionUC.NewJobTypesSelectedUseCase(
				l,
				pfilter.NewJobSearchFilterService(l, filterRepo),
				&stubJobSpecificResolver{},
				newStubJobTypeSearchToolResolver(),
			)
		},
	})

	e, err := newMockBootstrapServer(log, &Module{handler: handler})
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	rec := performJSONRequestWithHeader(e, http.MethodPost, "/positions/jobtypes/clear", `{}`, "session-jt-clear")
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
	}
	if strings.TrimSpace(rec.Body.String()) != "{}" {
		t.Fatalf("expected empty response, got %s", rec.Body.String())
	}

	var persisted jobfilter.JobSearchFilter
	if err := json.Unmarshal(filterRepo.lastJSON, &persisted); err != nil {
		t.Fatalf("failed to unmarshal persisted payload: %v", err)
	}
	if filterRepo.lastSession != "session-jt-clear" {
		t.Fatalf("expected session-jt-clear, got %s", filterRepo.lastSession)
	}
	group := persisted.Jobtypes[pcontracts.ToolNameSearchJobPostings]
	if len(group) != 3 {
		t.Fatalf("expected 3 jobtypes after clear, got %d", len(group))
	}
	for _, jt := range group {
		if jt.Selected {
			t.Fatalf("expected all jobtypes unselected, got %+v", jt)
		}
	}
	if persisted.Salary != 500 {
		t.Fatalf("expected other fields to be kept, salary=%d", persisted.Salary)
	}
}

func TestPositionAPIs_JobTypeSearchFilter_ReturnsOtherFiltersAndSelectedOptions(t *testing.T) {
	log := &tmock.MockLogger{}
	filterRepo := &stubJobSearchFilterRepo{
		current: &jobfilter.JobSearchFilter{
			Jobtypes: map[string][]*jobfilter.JobtypeSelectableItem{
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					{JobSearchFilterSelectableItem: jobfilter.JobSearchFilterSelectableItem{JobSearchFilterOtherFilterOption: jobfilter.JobSearchFilterOtherFilterOption{Label: "ITコンサルタント（アプリ）", Value: "ITコンサルタント（アプリ）"}, Selected: true}},
				},
			},
			SelectedOtherFilterOptions: map[string]map[string][]string{
				pcontracts.ToolNameSearchJobPostingsForITEngineer: {
					"言語（all）": {"Go"},
				},
			},
		},
	}

	jobSpecificParams.ITEngineerSearchFilters = []*jobfilter.JobSearchFilterOtherFilter{
		{Name: "言語（all）", Type: jobfilter.JobSearchFilterTypeMultiple, Options: []*jobfilter.JobSearchFilterOtherFilterOption{{Label: "Go", Value: "Go"}}},
	}

	handler := NewHandler(HandlerDependencies{
		NewJobTypeSearchFilterUseCase: func(l logger.LevelLogger) JobTypeSearchFilterUseCase {
			return positionUC.NewJobTypeSearchFilterUseCase(
				l,
				pfilter.NewJobSearchFilterService(l, filterRepo),
				&stubJobSpecificResolver{},
			)
		},
		JobTypeSearchToolResolver: newStubJobTypeSearchToolResolver(),
	})

	e, err := newMockBootstrapServer(log, &Module{handler: handler})
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	rec := performJSONRequestWithHeader(e, http.MethodGet, "/positions/search_filter/jobtype?JobtypeName=IT%E3%82%B3%E3%83%B3%E3%82%B5%E3%83%AB%E3%82%BF%E3%83%B3%E3%83%88%EF%BC%88%E3%82%A2%E3%83%97%E3%83%AA%EF%BC%89", "", "session-jt-filter")
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
	}

	var body struct {
		OtherFilters          []map[string]any    `json:"OtherFilters"`
		SelectedFilterOptions map[string][]string `json:"SelectedFilterOptions"`
	}
	if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
		t.Fatalf("invalid response json: %v", err)
	}
	if len(body.OtherFilters) == 0 {
		t.Fatalf("expected OtherFilters")
	}
	if got := body.SelectedFilterOptions["言語（all）"]; len(got) != 1 || got[0] != "Go" {
		t.Fatalf("unexpected SelectedFilterOptions: %+v", body.SelectedFilterOptions)
	}
}

func TestPositionAPIs_JobSpecificWithRealResolver(t *testing.T) {
	log := &tmock.MockLogger{}
	cache := &master.Cache{
		Prefectures:      master.Prefectures{{ID: master.PrefectureIDTokyo, Name: "東京都"}},
		Cities:           master.Cities{{ID: 139999, Name: "23区", PrefectureID: master.PrefectureIDTokyo}, {ID: 13101, Name: "千代田区", PrefectureID: master.PrefectureIDTokyo}},
		PrefectureCities: master.PrefectureCities{{PrefectureName: "東京都", CityName: "23区", RealCityName: "新宿区", CityID: 139999}},
		JobTypeSmalls: master.JobTypeSmalls{
			{ID: 10001, Name: "SE"},
			{ID: 20001, Name: "FS"},
		},
		Skills: master.Skills{
			{ID: 1, Name: master.SkillName("言語（all）$Go")},
			{ID: 2, Name: master.SkillName("取扱商材（金融商品）$保険")},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{TraitPositionID: master.PtjSalesStyleDive, Name: "あり", UserSideName: "あり", Value: 1},
			},
		},
	}
	setMasterCacheForRouteAPITest(cache)
	providerRepositoryRegistry := service.NewProviderRepositoryRegistry(log)
	cacheService := service.NewMiidasCacheService(log, makeRouteAPITestCacheProvider(cache), providerRepositoryRegistry)
	locationLookup := makeInitializedLocationLookupService(log, makeRouteAPITestCacheProvider(cache))
	resolver := positionUC.NewJobSpecificSearchResolver(cacheService, locationLookup)

	mv := &stubMVGateway{list: []*iface.PositionListEntry{{PositionId: 1}}}
	repo := &stubPositionRepo{
		byIDs: positionDomain.Positions{
			{ID: 1, Detail: positionDomain.Detail{Title: "summary title", MainJobText: "summary text"}},
		},
	}

	handler := NewHandler(HandlerDependencies{
		NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
			return positionUC.NewGenericSearchUseCase(l, mv, nil, nil, repo, &stubPositionValidator{}, &stubLocationLookup{})
		},
		NewDetailUseCase: func(l logger.LevelLogger) DetailUseCase {
			return positionUC.NewDetailUseCase(repo, &stubCompanyRepo{}, master.Provider(), l)
		},
		NewSummariesUseCase: func(l logger.LevelLogger) SummariesUseCase {
			return positionUC.NewSummariesUseCase(l, repo)
		},
		NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
			return positionUC.NewSearchWithJobTypeUseCase(l, mv, nil, nil, repo, resolver, nil, nil), nil
		},
	})
	e, err := newMockBootstrapServer(log, &Module{handler: handler})
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	rec := performJSONRequest(e, "/positions/search/it_engineer", `{
		"Salary":600,
		"JobtypeNames":["SE"],
		"Locations":[
			{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"},
			{"LocationType":"希望勤務地","PrefectureName":"東京都","CityName":"新宿区"}
		],
		"DayOffs":["土日祝休み"],
		"AverageOvertime":"10時間以内",
		"ProgrammingLanguages":["Go"]
	}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
	}

	rec = performJSONRequest(e, "/positions/search/financial_sales", `{
		"Salary":600,
		"JobtypeNames":["FS"],
		"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
		"SalesStyleDive":"あり"
	}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
	}
}

func setMasterCacheForRouteAPITest(cache *master.Cache) {
	cp := master.Provider()
	field := reflect.ValueOf(cp).Elem().FieldByName("cache")
	reflect.NewAt(field.Type(), unsafe.Pointer(field.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
}

func performJSONRequestWithHeader(e *echo.Echo, method, path, body, value string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, strings.NewReader(body))
	req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	if value != "" {
		req.Header.Set("X-Session-Id", value)
	}
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)
	return rec
}

func makeRouteAPITestCacheProvider(cache *master.Cache) *master.CacheProvider {
	cp := &master.CacheProvider{}
	field := reflect.ValueOf(cp).Elem().FieldByName("cache")
	reflect.NewAt(field.Type(), unsafe.Pointer(field.UnsafeAddr())).Elem().Set(reflect.ValueOf(cache))
	return cp
}
