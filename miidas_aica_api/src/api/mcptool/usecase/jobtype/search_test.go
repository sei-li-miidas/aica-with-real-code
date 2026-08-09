package jobtype

import (
	"errors"
	"testing"

	"github.com/pgvector/pgvector-go"

	mservice "aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	semanticService "aica/api/api/mcptool/usecase/shared/semantic"
	hydehistory "aica/api/domain/hyde_history"
	"aica/api/domain/jobtype"
	"aica/api/domain/provider"
	dsearch "aica/api/domain/search"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"

	"gorm.io/gorm"
)

type stubVectorizerRepository struct{}

func (s *stubVectorizerRepository) GenerateEmbedding(_ string) (*pgvector.Vector, error) {
	v := pgvector.NewVector([]float32{0.1})
	return &v, nil
}

func (s *stubVectorizerRepository) GenerateEmbeddings(_ []*vectorizer.EmbeddingTarget) ([]*vectorizer.EmbeddingResult, error) {
	return nil, nil
}

type stubHyDEResolver struct{}

func (s *stubHyDEResolver) ResolveJobTypeText(_ string, _ bool) (string, error)  { return "", nil }
func (s *stubHyDEResolver) ResolveIndustryText(_ string, _ bool) (string, error) { return "", nil }

type stubJobTypeSearcher struct {
	searchFn func(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*jobtype.JobTypeSearchResult, error)
}

func (s *stubJobTypeSearcher) Search(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*jobtype.JobTypeSearchResult, error) {
	return s.searchFn(params, limit, useHydeHistory)
}

type stubHydeHistoryRepo struct{}

func (s *stubHydeHistoryRepo) GetHydeText(hydehistory.HydeType, string) (*string, error) {
	return nil, nil
}
func (s *stubHydeHistoryRepo) Save(*hydehistory.HydeHistory) error { return nil }

type stubJobTypeSemanticRepo struct{}

func (s *stubJobTypeSemanticRepo) SemanticSearch(string, float64, func(*gorm.DB) *gorm.DB) ([]*jobtype.JobTypeSearchResult, error) {
	return nil, nil
}

func TestSearchUseCase_Execute_DelegatesToSemanticService(t *testing.T) {
	var gotVectorizerProvider provider.Provider
	deps := SearchUseCaseDependencies{
		NewVectorizerRepository: func(p provider.Provider) (vectorizer.VectorizerRepository, error) {
			gotVectorizerProvider = p
			return &stubVectorizerRepository{}, nil
		},
		NewHydeService: func(_ logger.LevelLogger, _ hydehistory.HydeHistoryFinderAndSaver) *mservice.HydeService {
			return &mservice.HydeService{}
		},
	}

	var gotHydeProvider provider.Provider
	deps.NewHydeResolver = func(_ *mservice.HydeService, p provider.Provider) (semanticService.HyDETextResolver, error) {
		gotHydeProvider = p
		return &stubHyDEResolver{}, nil
	}

	expected := []*jobtype.JobTypeSearchResult{{ID: 10}}
	var gotKeyword string
	var gotLimit uint
	var gotHistory bool
	deps.NewSearcher = func(
		_ logger.LevelLogger,
		_ semanticService.HyDETextResolver,
		_ semanticService.EmbeddingGenerator,
		_ dsearch.SemanticSearchRepository[*jobtype.JobTypeSearchResult],
	) semanticService.JobTypeSemanticSearcher {
		return &stubJobTypeSearcher{
			searchFn: func(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*jobtype.JobTypeSearchResult, error) {
				gotKeyword = params.Keyword
				gotLimit = limit
				gotHistory = useHydeHistory
				return expected, nil
			},
		}
	}

	params := http.NewDefaultVectorSearchParams("SE")
	params.Provider = string(provider.ProviderOpenAI)

	uc := NewSearchUseCaseWithRepositoriesAndDependencies(&tmock.MockLogger{}, &stubHydeHistoryRepo{}, &stubJobTypeSemanticRepo{}, deps)
	got, err := uc.Execute(&params, 5, true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(got) != 1 || got[0].ID != 10 {
		t.Fatalf("unexpected result: %#v", got)
	}
	if gotVectorizerProvider != provider.ProviderOpenAI {
		t.Fatalf("unexpected vectorizer provider: %v", gotVectorizerProvider)
	}
	if gotHydeProvider != provider.ProviderOpenAI {
		t.Fatalf("unexpected hyde provider: %v", gotHydeProvider)
	}
	if gotKeyword != "SE" || gotLimit != 5 || !gotHistory {
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
			return &stubHyDEResolver{}, nil
		},
		NewSearcher: func(
			_ logger.LevelLogger,
			_ semanticService.HyDETextResolver,
			_ semanticService.EmbeddingGenerator,
			_ dsearch.SemanticSearchRepository[*jobtype.JobTypeSearchResult],
		) semanticService.JobTypeSemanticSearcher {
			return &stubJobTypeSearcher{}
		},
	}

	params := http.NewDefaultVectorSearchParams("SE")
	params.Provider = string(provider.ProviderOpenAI)

	uc := NewSearchUseCaseWithRepositoriesAndDependencies(&tmock.MockLogger{}, &stubHydeHistoryRepo{}, &stubJobTypeSemanticRepo{}, deps)
	_, err := uc.Execute(&params, 5, true)
	if err == nil {
		t.Fatalf("expected error")
	}
}

func TestSearchUseCase_Execute_HydeResolverError(t *testing.T) {
	deps := SearchUseCaseDependencies{
		NewVectorizerRepository: func(_ provider.Provider) (vectorizer.VectorizerRepository, error) {
			return &stubVectorizerRepository{}, nil
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
			_ dsearch.SemanticSearchRepository[*jobtype.JobTypeSearchResult],
		) semanticService.JobTypeSemanticSearcher {
			return &stubJobTypeSearcher{}
		},
	}

	params := http.NewDefaultVectorSearchParams("SE")
	params.Provider = string(provider.ProviderOpenAI)

	uc := NewSearchUseCaseWithRepositoriesAndDependencies(&tmock.MockLogger{}, &stubHydeHistoryRepo{}, &stubJobTypeSemanticRepo{}, deps)
	_, err := uc.Execute(&params, 5, true)
	if err == nil {
		t.Fatalf("expected error")
	}
}
