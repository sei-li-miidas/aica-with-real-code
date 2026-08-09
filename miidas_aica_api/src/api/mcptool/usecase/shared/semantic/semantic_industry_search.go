package semantic

import (
	"aica/api/domain/industry"
	"aica/api/domain/search"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"

	"github.com/pkg/errors"
	"github.com/samber/lo"
)

type IndustrySemanticSearchService struct {
	logger       logger.LevelLogger
	hydeResolver HyDETextResolver
	embedding    EmbeddingGenerator
	repository   search.SemanticSearchRepository[*industry.IndustrySearchResult]
}

func NewIndustrySemanticSearchService(
	logger logger.LevelLogger,
	hydeResolver HyDETextResolver,
	embedding EmbeddingGenerator,
	repository search.SemanticSearchRepository[*industry.IndustrySearchResult],
) IndustrySemanticSearcher {
	return &IndustrySemanticSearchService{
		logger:       logger,
		hydeResolver: hydeResolver,
		embedding:    embedding,
		repository:   repository,
	}
}

func (s *IndustrySemanticSearchService) Search(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*industry.IndustrySearchResult, error) {
	hydeText, err := s.hydeResolver.ResolveIndustryText(params.Keyword, useHydeHistory)
	if err != nil {
		s.logger.Warn("HyDEテキストの取得・生成に失敗しました。", "keyword", params.Keyword, "error", err)
		hydeText = params.Keyword
	}

	embeddings, err := s.embedding.GenerateEmbedding(hydeText)
	if err != nil {
		return nil, err
	}

	industries, err := s.repository.SemanticSearch(embeddings.String(), params.Distance, nil)
	if err != nil {
		s.logger.Error("業種検索失敗しました。", "Vector Search Parameters", params, "error", errors.WithStack(err))
		return nil, err
	}

	uniqueIndustries := lo.Reduce(industries, func(acc []*industry.IndustrySearchResult, i1 *industry.IndustrySearchResult, _ int) []*industry.IndustrySearchResult {
		if _, found := lo.Find(acc, func(i2 *industry.IndustrySearchResult) bool {
			return i2.ID == i1.ID
		}); !found {
			acc = append(acc, i1)
		}
		return acc
	}, []*industry.IndustrySearchResult{})

	return lo.Subset(uniqueIndustries, 0, limit), nil
}
