package http

import "aica/api/domain/provider"

type (
	VectorSearchParams struct {
		Provider string
		Keyword  string
		Distance float64
	}
)

// キーワード以外はデフォルト設定
func NewDefaultVectorSearchParams(keyword string) VectorSearchParams {
	return VectorSearchParams{
		Provider: string(provider.DefaultProvider),
		Keyword:  keyword,
		Distance: DEFAULT_DISTANCE,
	}
}
