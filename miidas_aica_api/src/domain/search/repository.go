package search

import "gorm.io/gorm"

// SemanticSearchRepository は意味情報検索のリポジトリインターフェース
type SemanticSearchRepository[T any] interface {
	SemanticSearch(embedding string, distance float64, addConditions func(*gorm.DB) *gorm.DB) ([]T, error)
}
