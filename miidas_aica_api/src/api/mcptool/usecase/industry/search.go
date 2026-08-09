package industry

import (
	"aica/api/api/mcptool/service"
	semanticService "aica/api/api/mcptool/usecase/shared/semantic"
	hydehistory "aica/api/domain/hyde_history"
	"aica/api/domain/industry"
	"aica/api/domain/provider"
	"aica/api/domain/search"
	"aica/api/domain/vectorizer"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"
)

// SearchUseCase .
type SearchUseCase struct {
	logger          logger.LevelLogger
	hydeHistoryRepo hydehistory.HydeHistoryFinderAndSaver
	industryRepo    search.SemanticSearchRepository[*industry.IndustrySearchResult]
	deps            SearchUseCaseDependencies
}

type vectorizerRepositoryFactory func(provider.Provider) (vectorizer.VectorizerRepository, error)

type SearchUseCaseDependencies struct {
	NewVectorizerRepository vectorizerRepositoryFactory
	NewHydeService          func(logger.LevelLogger, hydehistory.HydeHistoryFinderAndSaver) *service.HydeService
	NewHydeResolver         func(*service.HydeService, provider.Provider) (semanticService.HyDETextResolver, error)
	NewSearcher             func(logger.LevelLogger, semanticService.HyDETextResolver, semanticService.EmbeddingGenerator, search.SemanticSearchRepository[*industry.IndustrySearchResult]) semanticService.IndustrySemanticSearcher
}

func NewSearchUseCaseWithRepositoriesAndDependencies(
	l logger.LevelLogger,
	hydeHistoryRepo hydehistory.HydeHistoryFinderAndSaver,
	industryRepo search.SemanticSearchRepository[*industry.IndustrySearchResult],
	deps SearchUseCaseDependencies,
) *SearchUseCase {
	if deps.NewVectorizerRepository == nil || deps.NewHydeService == nil || deps.NewHydeResolver == nil || deps.NewSearcher == nil {
		panic("all search usecase dependencies are required")
	}
	return &SearchUseCase{
		logger:          l,
		hydeHistoryRepo: hydeHistoryRepo,
		industryRepo:    industryRepo,
		deps:            deps,
	}
}

func (uc *SearchUseCase) Execute(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*industry.IndustrySearchResult, error) {
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
		uc.industryRepo,
	)
	return searcher.Search(params, limit, useHydeHistory)
}

// func (uc *SearchUseCase) industriesToCSV(industries []*industry.IndustrySmallVector) (string, error) {
// 	var sb strings.Builder
// 	writer := csv.NewWriter(&sb)

// 	// Write the header
// 	header := []string{"業種ID", "業種の説明"}
// 	if err := writer.Write(header); err != nil {
// 		return "", err
// 	}

// 	// Write the data rows
// 	for _, industry := range industries {
// 		row := []string{
// 			strconv.Itoa(industry.ID),
// 			industry.Description,
// 		}
// 		if err := writer.Write(row); err != nil {
// 			return "", err
// 		}
// 	}

// 	// Flush the writer to ensure all data is written
// 	writer.Flush()
// 	if err := writer.Error(); err != nil {
// 		return "", err
// 	}

// 	return sb.String(), nil
// }
