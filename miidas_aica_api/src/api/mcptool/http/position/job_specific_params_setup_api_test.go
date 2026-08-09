package position

import (
	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	positionUC "aica/api/api/mcptool/usecase/position"
	pfilter "aica/api/api/mcptool/usecase/position/filter"
	"aica/api/domain/public/master"
	positionDomain "aica/api/domain/user/apply/position"
	"aica/api/domain/user/apply/vo"
	"aica/api/sdk/logger"
	"encoding/json"
	"net/http"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"gorm.io/gorm"
)

func TestAJobSpecificSetup_BranchesViaAPI(t *testing.T) {
	log := &tmock.MockLogger{}
	cache := &master.Cache{
		Prefectures: master.Prefectures{
			{ID: master.PrefectureIDTokyo, Name: "東京都"},
		},
		Cities: master.Cities{
			{ID: 139999, Name: "23区", PrefectureID: master.PrefectureIDTokyo},
			{ID: 13101, Name: "千代田区", PrefectureID: master.PrefectureIDTokyo},
		},
		PrefectureCities: master.PrefectureCities{
			{PrefectureID: master.PrefectureIDTokyo, PrefectureName: "東京都", CityID: 139999, CityName: "23区", RealCityName: "新宿区"},
		},
		JobTypeSmalls: master.JobTypeSmalls{
			{ID: 10001, Name: "SE"},
			{ID: 20001, Name: "FS"},
		},
		SkillGroups: master.SkillGroups{
			{ID: 1, Name: "言語（all）"},
			{ID: 2, Name: "プロジェクト規模（IT）"},
			{ID: 11, Name: "取扱商材（金融商品）"},
			{ID: 12, Name: "営業スタイル（提案型／ルート型）"},
			{ID: 13, Name: "対象顧客（新規／既存）"},
			// intentionally missing: 開発案件種別（IT／業務系）
		},
		Skills: master.Skills{
			{ID: 1, SkillGroupID: 1, Name: "言語（all）$Go"},
			{ID: 2, SkillGroupID: 1, Name: "言語（all）$Go"}, // duplicate option branch
			{ID: 3, SkillGroupID: 2, Name: "プロジェクト規模（IT）$100人月"},
			{ID: 4, SkillGroupID: 11, Name: "取扱商材（金融商品）$保険"},
			{ID: 5, SkillGroupID: 12, Name: "営業スタイル（提案型／ルート型）$提案型"},
			{ID: 6, SkillGroupID: 13, Name: "対象顧客（新規／既存）$新規"},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{TraitPositionID: master.PtjSalesStyleDive, Name: "あり", UserSideName: "あり", Value: 1},
				{TraitPositionID: master.PtjSalesStyleDive, Name: "なし", UserSideName: "なし", Value: 2},
			},
		},
	}
	setMasterCacheForRouteAPITest(cache)
	providerRepositoryRegistry := service.NewProviderRepositoryRegistry(log)
	cacheService := service.NewMiidasCacheService(log, makeRouteAPITestCacheProvider(cache), providerRepositoryRegistry)

	// Trigger job_specific_params.Setup via module creation (same path as production bootstrap).
	_, err := NewModule(Dependencies{
		Logger:                     log,
		CacheService:               cacheService,
		ProviderRepositoryRegistry: providerRepositoryRegistry,
		LocationLookup:             makeInitializedLocationLookupService(log, makeRouteAPITestCacheProvider(cache)),
		MVGateway:                  &stubMVGateway{},
		AgentDBProvider:            func() *gorm.DB { return &gorm.DB{} },
		MiidasDBProvider:           func() *gorm.DB { return &gorm.DB{} },
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}

	mv := &stubMVGateway{list: []*iface.PositionListEntry{{PositionId: 1}}}
	repo := &stubPositionRepo{
		byID: &positionDomain.Position{
			ID:        1,
			CompanyID: 1,
			Detail: positionDomain.Detail{
				Title:          "detail title",
				EmploymentType: &vo.ValueText{ID: int(master.PositionEmploymentTypeIDEmployee)},
			},
		},
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
		NewSearchWithJobTypeUseCase: func(l logger.LevelLogger, enablePersistence bool) (SearchWithJobTypeUseCase, error) {
			var fs *pfilter.JobSearchFilterService
			if enablePersistence {
				fs = pfilter.NewJobSearchFilterService(l, &stubJobSearchFilterRepo{})
			}
			return positionUC.NewSearchWithJobTypeUseCase(l, mv, nil, nil, repo, &stubJobSpecificResolver{}, fs, fs), nil
		},
	})
	e, err := newMockBootstrapServer(log, &Module{handler: handler})
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	// IT endpoint response reflects setup result.
	itRec := performJSONRequest(e, "/positions/search/it_engineer", `{
		"Salary":600,
		"JobtypeNames":["SE"],
		"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
		"ProgrammingLanguages":["Go"]
	}`)
	if itRec.Code != http.StatusOK {
		t.Fatalf("it endpoint expected 200 got %d body=%s", itRec.Code, itRec.Body.String())
	}
	assertFilterNames(t, itRec.Body.Bytes(), []string{"言語（all）", "プロジェクト規模（IT）"}, []string{"開発案件種別（IT／業務系）"})

	// Financial endpoint response reflects setup result.
	finRec := performJSONRequest(e, "/positions/search/financial_sales", `{
		"Salary":600,
		"JobtypeNames":["FS"],
		"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]
	}`)
	if finRec.Code != http.StatusOK {
		t.Fatalf("financial endpoint expected 200 got %d body=%s", finRec.Code, finRec.Body.String())
	}
	assertFilterNames(t, finRec.Body.Bytes(), []string{"取扱商材（金融商品）", "営業スタイル（提案型／ルート型）", "対象顧客（新規／既存）", "新規飛び込み"}, nil)
}

func assertFilterNames(t *testing.T, body []byte, mustInclude []string, mustExclude []string) {
	t.Helper()
	var resp struct {
		SearchFilters struct {
			OtherFilters map[string][]struct {
				Name string
			}
		}
	}
	if err := json.Unmarshal(body, &resp); err != nil {
		t.Fatalf("failed to parse response json: %v", err)
	}
	set := map[string]bool{}
	for _, filters := range resp.SearchFilters.OtherFilters {
		for _, f := range filters {
			set[f.Name] = true
		}
	}
	for _, name := range mustInclude {
		if !set[name] {
			t.Fatalf("expected filter %q to exist", name)
		}
	}
	for _, name := range mustExclude {
		if set[name] {
			t.Fatalf("expected filter %q to be absent", name)
		}
	}
}
