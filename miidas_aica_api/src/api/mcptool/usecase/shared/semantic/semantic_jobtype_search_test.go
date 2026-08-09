package semantic

import (
	tmock "aica/api/api/mcptool/testutil/mock"
	"aica/api/domain/jobtype"
	"aica/api/domain/search"
	"aica/api/sdk/http"
	"testing"

	"github.com/pgvector/pgvector-go"
	"gorm.io/gorm"
)

type stubHyDETextResolver struct {
	jobTypeText  string
	jobTypeErr   error
	industryText string
	industryErr  error
}

func (s *stubHyDETextResolver) ResolveJobTypeText(_ string, _ bool) (string, error) {
	return s.jobTypeText, s.jobTypeErr
}
func (s *stubHyDETextResolver) ResolveIndustryText(_ string, _ bool) (string, error) {
	return s.industryText, s.industryErr
}

type stubEmbeddingGenerator struct {
	errByText map[string]error
}

func (s *stubEmbeddingGenerator) GenerateEmbedding(text string) (*pgvector.Vector, error) {
	if s.errByText != nil {
		if err := s.errByText[text]; err != nil {
			return nil, err
		}
	}
	v := pgvector.NewVector([]float32{0.1, 0.2, 0.3})
	return &v, nil
}

type stubJobTypeSemanticRepository struct {
	err     error
	results []*jobtype.JobTypeSearchResult
}

func (s *stubJobTypeSemanticRepository) SemanticSearch(_ string, _ float64, _ func(*gorm.DB) *gorm.DB) ([]*jobtype.JobTypeSearchResult, error) {
	if s.err != nil {
		return nil, s.err
	}
	return s.results, nil
}

var _ HyDETextResolver = (*stubHyDETextResolver)(nil)
var _ EmbeddingGenerator = (*stubEmbeddingGenerator)(nil)
var _ search.SemanticSearchRepository[*jobtype.JobTypeSearchResult] = (*stubJobTypeSemanticRepository)(nil)

func TestJobTypeSemanticSearchService_Search_JSON(t *testing.T) {
	svc := NewJobTypeSemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{jobTypeText: `[{"job_description":"desc1"},{"job_description":"desc2"}]`},
		&stubEmbeddingGenerator{},
		&stubJobTypeSemanticRepository{
			results: []*jobtype.JobTypeSearchResult{
				{ID: 1, Distance: 0.11},
				{ID: 1, Distance: 0.12},
				{ID: 2, Distance: 0.13},
			},
		},
	)
	params := http.NewDefaultVectorSearchParams("SE")
	results, err := svc.Search(&params, 5, true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) == 0 {
		t.Fatalf("expected results")
	}
}

func TestJobTypeSemanticSearchService_Search_FallbackPlainText(t *testing.T) {
	svc := NewJobTypeSemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{jobTypeText: `plain text`},
		&stubEmbeddingGenerator{},
		&stubJobTypeSemanticRepository{
			results: []*jobtype.JobTypeSearchResult{
				{ID: 1, Distance: 0.11},
			},
		},
	)
	params := http.NewDefaultVectorSearchParams("SE")
	results, err := svc.Search(&params, 5, true)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 1 || results[0].ID != 1 {
		t.Fatalf("unexpected results: %#v", results)
	}
}

func TestJobTypeSemanticSearchService_Search_ErrorPaths(t *testing.T) {
	svc1 := NewJobTypeSemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{jobTypeText: `plain text`},
		&stubEmbeddingGenerator{errByText: map[string]error{"plain text": assertErr("embed failed")}},
		&stubJobTypeSemanticRepository{},
	)
	params := http.NewDefaultVectorSearchParams("SE")
	_, err := svc1.Search(&params, 5, true)
	if err == nil {
		t.Fatalf("expected embedding error")
	}

	svc2 := NewJobTypeSemanticSearchService(
		&tmock.MockLogger{},
		&stubHyDETextResolver{jobTypeText: `plain text`},
		&stubEmbeddingGenerator{},
		&stubJobTypeSemanticRepository{err: assertErr("repo failed")},
	)
	params2 := http.NewDefaultVectorSearchParams("SE")
	_, err = svc2.Search(&params2, 5, true)
	if err == nil {
		t.Fatalf("expected repository error")
	}
}

type errorString string

func (e errorString) Error() string { return string(e) }

func assertErr(msg string) error { return errorString(msg) }
