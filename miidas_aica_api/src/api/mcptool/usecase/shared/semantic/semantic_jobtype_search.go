package semantic

import (
	"aica/api/domain/hyde"
	"aica/api/domain/jobtype"
	"aica/api/domain/search"
	"aica/api/sdk/http"
	"aica/api/sdk/logger"
	"aica/api/sdk/util"
	"encoding/json"
	"sort"
	"sync"

	"github.com/pkg/errors"
	"github.com/samber/lo"
)

type JobTypeSemanticSearchService struct {
	logger       logger.LevelLogger
	hydeResolver HyDETextResolver
	embedding    EmbeddingGenerator
	repository   search.SemanticSearchRepository[*jobtype.JobTypeSearchResult]
}

func NewJobTypeSemanticSearchService(
	logger logger.LevelLogger,
	hydeResolver HyDETextResolver,
	embedding EmbeddingGenerator,
	repository search.SemanticSearchRepository[*jobtype.JobTypeSearchResult],
) JobTypeSemanticSearcher {
	return &JobTypeSemanticSearchService{
		logger:       logger,
		hydeResolver: hydeResolver,
		embedding:    embedding,
		repository:   repository,
	}
}

func (s *JobTypeSemanticSearchService) Search(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*jobtype.JobTypeSearchResult, error) {
	hydeText, err := s.hydeResolver.ResolveJobTypeText(params.Keyword, useHydeHistory)
	if err != nil {
		s.logger.Warn("HyDEテキストの取得・生成に失敗しました。", "keyword", params.Keyword, "error", err)
		hydeText = params.Keyword
	}

	var hydeResponse []*hyde.JobTypeHydeResponse
	if err := json.Unmarshal([]byte(hydeText), &hydeResponse); err != nil {
		s.logger.Info("HyDEテキストのjson.Unmarshalに失敗しました。Plain textでの意味情報検索を実行する", "hydeText", hydeText, "error", err)
		return s.simpleSearch(hydeText, params.Distance)
	}

	type searchResult struct {
		jobtypes []*jobtype.JobTypeSearchResult
		err      error
	}
	resultChan := make(chan searchResult, len(hydeResponse))
	var wg sync.WaitGroup
	for _, item := range hydeResponse {
		wg.Add(1)
		go func(jobDesc string) {
			defer wg.Done()
			jobtypes, err := s.simpleSearch(jobDesc, params.Distance)
			resultChan <- searchResult{jobtypes: jobtypes, err: err}
		}(item.JobDescription)
	}
	go func() {
		wg.Wait()
		close(resultChan)
	}()

	allJobTypes := make([]*jobtype.JobTypeSearchResult, 0)
	for result := range resultChan {
		if result.err != nil {
			s.logger.Error("職種検索失敗しました。", "error", errors.WithStack(result.err))
			continue
		}
		allJobTypes = append(allJobTypes, result.jobtypes...)
	}

	uniqueJobTypes := lo.Reduce(allJobTypes, func(acc []*jobtype.JobTypeSearchResult, j1 *jobtype.JobTypeSearchResult, _ int) []*jobtype.JobTypeSearchResult {
		if _, found := lo.Find(acc, func(j2 *jobtype.JobTypeSearchResult) bool {
			return j2.ID == j1.ID
		}); !found {
			acc = append(acc, j1)
		}
		return acc
	}, []*jobtype.JobTypeSearchResult{})

	sort.Slice(uniqueJobTypes, func(i, j int) bool {
		return uniqueJobTypes[i].Distance < uniqueJobTypes[j].Distance
	})

	filteredResult, err := util.FilterBySteepestDrop(uniqueJobTypes, util.DefaultMinGap, func(j *jobtype.JobTypeSearchResult) float64 {
		return j.Distance
	})
	if err != nil {
		s.logger.Error("フィルタリングに失敗しました。", "error", err)
		return nil, err
	}
	return lo.Subset(filteredResult, 0, limit), nil
}

func (s *JobTypeSemanticSearchService) simpleSearch(text string, distance float64) ([]*jobtype.JobTypeSearchResult, error) {
	embeddings, err := s.embedding.GenerateEmbedding(text)
	if err != nil {
		s.logger.Error("simpleJobTypeVectorSearch エンベディング生成に失敗しました。", "hyDEText", text, "error", err)
		return nil, err
	}
	jobtypes, err := s.repository.SemanticSearch(embeddings.String(), distance, nil)
	if err != nil {
		s.logger.Error("職種の意味情報検索に失敗しました。", "hyDEText", text, "error", errors.WithStack(err))
		return nil, err
	}
	return jobtypes, nil
}
