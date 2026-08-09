package params

import (
	"testing"

	"aica/api/domain/public/master"
)

func TestSetup_NilCacheServiceReturnsError(t *testing.T) {
	if err := Setup(nil); err == nil {
		t.Fatalf("expected error for nil cache service")
	}
}

func TestBuildSkillFilter(t *testing.T) {
	cacheService := newCacheServiceForJobSpecific(&master.Cache{
		SkillGroups: []*master.SkillGroup{
			{ID: 1, Name: "言語（all）"},
		},
		Skills: []*master.Skill{
			{ID: 1, Name: "言語（all）$Go", SkillGroupID: 1},
			{ID: 2, Name: "言語（all）$Go", SkillGroupID: 1},
			{ID: 3, Name: "言語（all）$Java", SkillGroupID: 1},
		},
	})

	if got := buildSkillFilter(cacheService, "存在しない"); got != nil {
		t.Fatalf("expected nil")
	}

	got := buildSkillFilter(cacheService, "言語（all）")
	if got == nil || len(got.Options) != 2 {
		t.Fatalf("unexpected filter: %#v", got)
	}
}

func TestBuildSkillFilterByGroupID(t *testing.T) {
	cacheService := newCacheServiceForJobSpecific(&master.Cache{
		SkillGroups: []*master.SkillGroup{
			{ID: 11, Name: "取扱商材（金融商品）"},
		},
		Skills: []*master.Skill{
			{ID: 1, Name: "取扱商材（金融商品）$保険", SkillGroupID: 11},
			{ID: 2, Name: "取扱商材（金融商品）$保険", SkillGroupID: 11},
			{ID: 3, Name: "取扱商材（金融商品）$証券", SkillGroupID: 11},
		},
	})

	got := buildSkillFilterByGroupID(cacheService, 11, "fallback")
	if got == nil {
		t.Fatalf("expected filter")
	}
	if got.Name != "取扱商材（金融商品）" {
		t.Fatalf("expected group name, got: %s", got.Name)
	}
	if len(got.Options) != 2 {
		t.Fatalf("unexpected options: %#v", got.Options)
	}
}

func TestSetup_SuccessAndReinitialize(t *testing.T) {
	origIT, origFin := ITEngineerSearchFilters, FinancialSalesSearchFilters
	defer func() {
		ITEngineerSearchFilters = origIT
		FinancialSalesSearchFilters = origFin
	}()

	cacheService := newCacheServiceForJobSpecific(&master.Cache{
		SkillGroups: []*master.SkillGroup{
			{ID: 1, Name: "言語（all）"},
			{ID: 2, Name: "プロジェクト規模（IT）"},
			{ID: 5, Name: "アプリケーションフレームワーク（IT）"},
			{ID: 6, Name: "クラウドサービス（IT）"},
			{ID: 7, Name: "担当フェーズ（IT）"},
			{ID: 8, Name: "ポジション（IT）"},
			{ID: 9, Name: "システム規模（IT）"},
			{ID: 10, Name: "開発案件種別（IT／業務系）"},
			{ID: 11, Name: "取扱商材（金融商品）"},
			{ID: 12, Name: "営業スタイル（提案型／ルート型）"},
			{ID: 13, Name: "対象顧客（新規／既存）"},
		},
		Skills: []*master.Skill{
			{ID: 1, Name: "言語（all）$Go", SkillGroupID: 1},
			{ID: 2, Name: "取扱商材（金融商品）$保険", SkillGroupID: 11},
			{ID: 3, Name: "営業スタイル（提案型／ルート型）$提案型", SkillGroupID: 12},
			{ID: 4, Name: "対象顧客（新規／既存）$新規", SkillGroupID: 13},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{Value: 1, UserSideName: "あり"},
				{Value: 2, UserSideName: "なし"},
			},
		},
	})

	if err := Setup(cacheService); err != nil {
		t.Fatalf("unexpected setup error: %v", err)
	}
	if len(ITEngineerSearchFilters) == 0 || len(FinancialSalesSearchFilters) == 0 {
		t.Fatalf("expected initialized filters")
	}

	if err := Setup(nil); err == nil {
		t.Fatalf("expected nil cache service to return error")
	}

	reinitialized := newCacheServiceForJobSpecific(&master.Cache{
		SkillGroups: []*master.SkillGroup{
			{ID: 21, Name: "言語（all）"},
			{ID: 22, Name: "取扱商材（金融商品）"},
			{ID: 23, Name: "営業スタイル（提案型／ルート型）"},
			{ID: 24, Name: "対象顧客（新規／既存）"},
		},
		Skills: []*master.Skill{
			{ID: 100, Name: "言語（all）$Rust", SkillGroupID: 21},
			{ID: 101, Name: "取扱商材（金融商品）$投資信託", SkillGroupID: 22},
			{ID: 102, Name: "営業スタイル（提案型／ルート型）$ルート型", SkillGroupID: 23},
			{ID: 103, Name: "対象顧客（新規／既存）$既存", SkillGroupID: 24},
		},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {
				{Value: 1, UserSideName: "なし"},
			},
		},
	})
	if err := Setup(reinitialized); err != nil {
		t.Fatalf("unexpected setup error on reinitialize: %v", err)
	}

	itLanguageFilter := findFilterByName(ITEngineerSearchFilters, "言語（all）")
	if itLanguageFilter == nil || len(itLanguageFilter.Options) != 1 || itLanguageFilter.Options[0].Value != "Rust" {
		t.Fatalf("expected reinitialized IT language options, got: %#v", itLanguageFilter)
	}
}

func TestInitITEngineerSearchFilters_SkipNilAndEmptyOptions(t *testing.T) {
	orig := ITEngineerSearchFilters
	defer func() { ITEngineerSearchFilters = orig }()

	cacheService := newCacheServiceForJobSpecific(&master.Cache{
		SkillGroups: []*master.SkillGroup{
			{ID: 1, Name: "言語（all）"},
		},
		Skills: []*master.Skill{},
	})

	initITEngineerSearchFilters(cacheService)
	if len(ITEngineerSearchFilters) != 0 {
		t.Fatalf("expected no filters when options are empty or groups are missing")
	}
}

func TestInitFinancialSalesSearchFilters_SkipNilAndEmptyOptions(t *testing.T) {
	orig := FinancialSalesSearchFilters
	defer func() { FinancialSalesSearchFilters = orig }()

	cacheService := newCacheServiceForJobSpecific(&master.Cache{
		SkillGroups: []*master.SkillGroup{
			{ID: 1, Name: "取扱商材（金融商品）"},
		},
		Skills: []*master.Skill{},
		TraitPositionOptions: map[master.MasterTraitPositionID][]*master.TraitPositionOption{
			master.PtjSalesStyleDive: {},
		},
	})

	initFinancialSalesSearchFilters(cacheService)
	if len(FinancialSalesSearchFilters) == 0 {
		t.Fatalf("expected non-skill filters to be added")
	}
	if FinancialSalesSearchFilters[0].Name == "取扱商材（金融商品）" {
		t.Fatalf("expected empty option skill filter to be skipped")
	}
}
