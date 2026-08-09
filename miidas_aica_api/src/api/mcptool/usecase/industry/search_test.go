package industry

import (
	"errors"
	"testing"

	"github.com/pgvector/pgvector-go"

	mservice "aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	semanticService "aica/api/api/mcptool/usecase/shared/semantic"
	hydehistory "aica/api/domain/hyde_history"
	"aica/api/domain/industry"
	"aica/api/domain/provider"
	dsearch "aica/api/domain/search"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"

	"gorm.io/gorm"
)

type stubIndustryVectorizerRepository struct{}

func (s *stubIndustryVectorizerRepository) GenerateEmbedding(_ string) (*pgvector.Vector, error) {
	v := pgvector.NewVector([]float32{0.1})
	return &v, nil
}

func (s *stubIndustryVectorizerRepository) GenerateEmbeddings(_ []*vectorizer.EmbeddingTarget) ([]*vectorizer.EmbeddingResult, error) {
	return nil, nil
}

type stubIndustryHyDEResolver struct{}

func (s *stubIndustryHyDEResolver) ResolveJobTypeText(_ string, _ bool) (string, error) {
	return "", nil
}
func (s *stubIndustryHyDEResolver) ResolveIndustryText(_ string, _ bool) (string, error) {
	return "", nil
}

type stubIndustrySearcher struct {
	searchFn func(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*industry.IndustrySearchResult, error)
}

func (s *stubIndustrySearcher) Search(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*industry.IndustrySearchResult, error) {
	return s.searchFn(params, limit, useHydeHistory)
}

type stubIndustryHydeHistoryRepo struct{}

func (s *stubIndustryHydeHistoryRepo) GetHydeText(hydehistory.HydeType, string) (*string, error) {
	return nil, nil
}
func (s *stubIndustryHydeHistoryRepo) Save(*hydehistory.HydeHistory) error { return nil }

type stubIndustrySemanticRepo struct{}

func (s *stubIndustrySemanticRepo) SemanticSearch(string, float64, func(*gorm.DB) *gorm.DB) ([]*industry.IndustrySearchResult, error) {
	return nil, nil
}

func TestSearchUseCase_Execute_DelegatesToSemanticService(t *testing.T) {
	var gotVectorizerProvider provider.Provider
	deps := SearchUseCaseDependencies{
		NewVectorizerRepository: func(p provider.Provider) (vectorizer.VectorizerRepository, error) {
			gotVectorizerProvider = p
			return &stubIndustryVectorizerRepository{}, nil
		},
		NewHydeService: func(_ logger.LevelLogger, _ hydehistory.HydeHistoryFinderAndSaver) *mservice.HydeService {
			return &mservice.HydeService{}
		},
	}

	var gotHydeProvider provider.Provider
	deps.NewHydeResolver = func(_ *mservice.HydeService, p provider.Provider) (semanticService.HyDETextResolver, error) {
		gotHydeProvider = p
		return &stubIndustryHyDEResolver{}, nil
	}

	expected := []*industry.IndustrySearchResult{{ID: 20}}
	var gotKeyword string
	var gotLimit uint
	var gotHistory bool
	deps.NewSearcher = func(
		_ logger.LevelLogger,
		_ semanticService.HyDETextResolver,
		_ semanticService.EmbeddingGenerator,
		_ dsearch.SemanticSearchRepository[*industry.IndustrySearchResult],
	) semanticService.IndustrySemanticSearcher {
		return &stubIndustrySearcher{
			searchFn: func(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*industry.IndustrySearchResult, error) {
				gotKeyword = params.Keyword
				gotLimit = limit
				gotHistory = useHydeHistory
				return expected, nil
			},
		}
	}

	params := http.NewDefaultVectorSearchParams("SaaS")
	params.Provider = string(provider.ProviderOpenAI)

	uc := NewSearchUseCaseWithRepositoriesAndDependencies(&tmock.MockLogger{}, &stubIndustryHydeHistoryRepo{}, &stubIndustrySemanticRepo{}, deps)
	got, err := uc.Execute(&params, 7, true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(got) != 1 || got[0].ID != 20 {
		t.Fatalf("unexpected result: %#v", got)
	}
	if gotVectorizerProvider != provider.ProviderOpenAI {
		t.Fatalf("unexpected vectorizer provider: %v", gotVectorizerProvider)
	}
	if gotHydeProvider != provider.ProviderOpenAI {
		t.Fatalf("unexpected hyde provider: %v", gotHydeProvider)
	}
	if gotKeyword != "SaaS" || gotLimit != 7 || !gotHistory {
		t.Fatalf("unexpected delegated args keyword=%s limit=%d history=%v", gotKeyword, gotLimit, gotHistory)
	}
}

func TestSearchUseCase_Execute_VectorizerError(t *testing.T) {
	deps := SearchUseCaseDependencies{
		NewVectorizerRepository: func(_ provider.Provider) (vectorizer.VectorizerRepository, error) {
			return nil, errors.New("vectorizer failed")
		},
		NewHydeService: func(_ logger.LevelLogger, _ hydehistory.HydeHistoryFinderAndSaver) *mservice.HydeService {
			return &mservice.HydeService{}
		},
		NewHydeResolver: func(_ *mservice.HydeService, _ provider.Provider) (semanticService.HyDETextResolver, error) {
			return &stubIndustryHyDEResolver{}, nil
		},
		NewSearcher: func(
			_ logger.LevelLogger,
			_ semanticService.HyDETextResolver,
			_ semanticService.EmbeddingGenerator,
			_ dsearch.SemanticSearchRepository[*industry.IndustrySearchResult],
		) semanticService.IndustrySemanticSearcher {
			return &stubIndustrySearcher{}
		},
	}

	params := http.NewDefaultVectorSearchParams("SaaS")
	params.Provider = string(provider.ProviderOpenAI)

	uc := NewSearchUseCaseWithRepositoriesAndDependencies(&tmock.MockLogger{}, &stubIndustryHydeHistoryRepo{}, &stubIndustrySemanticRepo{}, deps)
	_, err := uc.Execute(&params, 7, true)
	if err == nil {
		t.Fatalf("expected error")
	}
}

func TestSearchUseCase_Execute_HydeResolverError(t *testing.T) {
	deps := SearchUseCaseDependencies{
		NewVectorizerRepository: func(_ provider.Provider) (vectorizer.VectorizerRepository, error) {
			return &stubIndustryVectorizerRepository{}, nil
		},
		NewHydeService: func(_ logger.LevelLogger, _ hydehistory.HydeHistoryFinderAndSaver) *mservice.HydeService {
			return &mservice.HydeService{}
		},
		NewHydeResolver: func(_ *mservice.HydeService, _ provider.Provider) (semanticService.HyDETextResolver, error) {
			return nil, errors.New("hyde resolver failed")
		},
		NewSearcher: func(
			_ logger.LevelLogger,
			_ semanticService.HyDETextResolver,
			_ semanticService.EmbeddingGenerator,
			_ dsearch.SemanticSearchRepository[*industry.IndustrySearchResult],
		) semanticService.IndustrySemanticSearcher {
			return &stubIndustrySearcher{}
		},
	}

	params := http.NewDefaultVectorSearchParams("SaaS")
	params.Provider = string(provider.ProviderOpenAI)

	uc := NewSearchUseCaseWithRepositoriesAndDependencies(&tmock.MockLogger{}, &stubIndustryHydeHistoryRepo{}, &stubIndustrySemanticRepo{}, deps)
	_, err := uc.Execute(&params, 7, true)
	if err == nil {
		t.Fatalf("expected error")
	}
}
