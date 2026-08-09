package importance

// Importance 重要度
type Importance int

const (
	ImportanceAnything   Importance = 0 // 不問
	ImportanceIfPossible Importance = 1 // 一致すれば嬉しい
	ImportanceImportant  Importance = 2 // 可能な限り重視したい
	ImportanceRequired   Importance = 3 // 必須
)

// IsAnything 「不問」かどうかを返す
func (i Importance) IsAnything() bool {
	return i == ImportanceAnything
}

// IsIfPossible 「一致すれば嬉しい」かどうかを返す
func (i Importance) IsIfPossible() bool {
	return i == ImportanceIfPossible
}

// IsImportant 「可能な限り重視したい」かどうかを返す
func (i Importance) IsImportant() bool {
	return i == ImportanceImportant
}

// IsRequired 「必須」かどうかを返す
func (i Importance) IsRequired() bool {
	return i == ImportanceRequired
}
