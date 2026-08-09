package jobtype

import (
	"aica/api/api/mcptool/service"
	semanticService "aica/api/api/mcptool/usecase/shared/semantic"
	hydehistory "aica/api/domain/hyde_history"
	"aica/api/domain/jobtype"
	"aica/api/domain/provider"
	"aica/api/domain/search"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"
)

type (
	vectorizerRepositoryFactory func(provider.Provider) (vectorizer.VectorizerRepository, error)

	// SearchUseCase .
	SearchUseCase struct {
		logger          logger.LevelLogger
		hydeHistoryRepo hydehistory.HydeHistoryFinderAndSaver
		jobTypeRepo     search.SemanticSearchRepository[*jobtype.JobTypeSearchResult]
		deps            SearchUseCaseDependencies
	}

	// 職種の意味情報検索のリクエスト
	SearchSemanticJobTypesRequest struct {
		Keyword  string
		Provider *string
		Distance *float64
		Limit    *uint
	}
)

type SearchUseCaseDependencies struct {
	NewVectorizerRepository vectorizerRepositoryFactory
	NewHydeService          func(logger.LevelLogger, hydehistory.HydeHistoryFinderAndSaver) *service.HydeService
	NewHydeResolver         func(*service.HydeService, provider.Provider) (semanticService.HyDETextResolver, error)
	NewSearcher             func(logger.LevelLogger, semanticService.HyDETextResolver, semanticService.EmbeddingGenerator, search.SemanticSearchRepository[*jobtype.JobTypeSearchResult]) semanticService.JobTypeSemanticSearcher
}

func NewSearchUseCaseWithRepositoriesAndDependencies(
	l logger.LevelLogger,
	hydeHistoryRepo hydehistory.HydeHistoryFinderAndSaver,
	jobTypeRepo search.SemanticSearchRepository[*jobtype.JobTypeSearchResult],
	deps SearchUseCaseDependencies,
) *SearchUseCase {
	if deps.NewVectorizerRepository == nil || deps.NewHydeService == nil || deps.NewHydeResolver == nil || deps.NewSearcher == nil {
		panic("all search usecase dependencies are required")
	}
	return &SearchUseCase{
		logger:          l,
		hydeHistoryRepo: hydeHistoryRepo,
		jobTypeRepo:     jobTypeRepo,
		deps:            deps,
	}
}

// Execute 検索
func (uc *SearchUseCase) Execute(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*jobtype.JobTypeSearchResult, error) {
	vectorizerProvider, err := uc.deps.NewVectorizerRepository(provider.Provider(params.Provider))
	if err != nil {
		return nil, err
	}

	hydeResolver, err := uc.deps.NewHydeResolver(
		uc.deps.NewHydeService(uc.logger, uc.hydeHistoryRepo),
		provider.Provider(params.Provider),
	)
	if err != nil {
		return nil, err
	}
	searcher := uc.deps.NewSearcher(
		uc.logger,
		hydeResolver,
		vectorizerProvider,
		uc.jobTypeRepo,
	)
	return searcher.Search(params, limit, useHydeHistory)
}
