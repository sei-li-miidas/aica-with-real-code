package semantic

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/industry"
	"aica/api/domain/search"
	"aica/api/sdk/http"
	"testing"

	"gorm.io/gorm"
)

type stubIndustrySemanticRepository struct {
	err     error
	results []*industry.IndustrySearchResult
}

func (s *stubIndustrySemanticRepository) SemanticSearch(_ string, _ float64, _ func(*gorm.DB) *gorm.DB) ([]*industry.IndustrySearchResult, error) {
	if s.err != nil {
		return nil, s.err
	}
	return s.results, nil
}

var _ search.SemanticSearchRepository[*industry.IndustrySearchResult] = (*stubIndustrySemanticRepository)(nil)

func TestIndustrySemanticSearchService_Search(t *testing.T) {
	svc := NewIndustrySemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{industryText: "industry hyde text"},
		&stubEmbeddingGenerator{},
		&stubIndustrySemanticRepository{
			results: []*industry.IndustrySearchResult{
				{ID: 10},
				{ID: 10},
				{ID: 20},
			},
		},
	)
	params := http.NewDefaultVectorSearchParams("saas")
	results, err := svc.Search(&params, 20, true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 2 {
		t.Fatalf("expected deduped results, got: %#v", results)
	}
}

func TestIndustrySemanticSearchService_Search_ErrorPaths(t *testing.T) {
	params := http.NewDefaultVectorSearchParams("saas")
	_, err := NewIndustrySemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{industryText: "industry hyde text"},
		&stubEmbeddingGenerator{errByText: map[string]error{"industry hyde text": errorString("embed failed")}},
		&stubIndustrySemanticRepository{},
	).Search(&params, 20, true)
	if err == nil {
		t.Fatalf("expected embedding error")
	}

	_, err = NewIndustrySemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{industryText: "industry hyde text"},
		&stubEmbeddingGenerator{},
		&stubIndustrySemanticRepository{err: errorString("repo failed")},
	).Search(&params, 20, true)
	if err == nil {
		t.Fatalf("expected repository error")
	}
}
