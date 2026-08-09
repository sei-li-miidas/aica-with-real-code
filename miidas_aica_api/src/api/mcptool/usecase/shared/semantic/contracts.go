package semantic

import (
	"aica/api/domain/industry"
	"aica/api/domain/jobtype"
	"aica/api/sdk/http"

	"github.com/pgvector/pgvector-go"
)

type HyDETextResolver interface {
	ResolveJobTypeText(keyword string, useHistory bool) (string, error)
	ResolveIndustryText(keyword string, useHistory bool) (string, error)
}

type EmbeddingGenerator interface {
	GenerateEmbedding(text string) (*pgvector.Vector, error)
}

type JobTypeSemanticSearcher interface {
	Search(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*jobtype.JobTypeSearchResult, error)
}

type IndustrySemanticSearcher interface {
	Search(params *http.VectorSearchParams, limit uint, useHydeHistory bool) ([]*industry.IndustrySearchResult, error)
}
