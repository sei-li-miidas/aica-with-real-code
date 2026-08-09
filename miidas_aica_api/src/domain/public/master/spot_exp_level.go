package master

import (
	"cmp"
	"slices"

	"github.com/samber/lo"

	"aica/api/sdk/slice"
)

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=SpotExpLevelPattern

// SpotExpLevelID スポット熟練度ID
type SpotExpLevelID int

// SpotExpLevelPattern スポット熟練度パターン
type SpotExpLevelPattern string

// SpotExpLevel スポット熟練度
type SpotExpLevel struct {
	ID        SpotExpLevelID      // ID
	Pattern   SpotExpLevelPattern // 熟練度パターン
	ClassNo   int                 // 分類No
	Label     string              // 熟練度ラベル
	SortOrder int                 // ソート順
}

func (s SpotExpLevel) GetID() SpotExpLevelID {
	return s.ID
}

// TableName .
func (s SpotExpLevel) TableName() string {
	return "master.spot_exp_level"
}

type (
	SpotExpLevels   []*SpotExpLevel
	SpotExpLevelMap = Map[SpotExpLevelID, SpotExpLevel]
)

func (s SpotExpLevels) ToMap() map[SpotExpLevelID]*SpotExpLevel {
	return lo.SliceToMap(s, func(e *SpotExpLevel) (SpotExpLevelID, *SpotExpLevel) {
		return e.ID, e
	})
}

func (s SpotExpLevels) GetByPattern(p SpotExpLevelPattern) SpotExpLevels {
	return slice.Filter(s, func(_ int, e *SpotExpLevel) bool {
		return e.Pattern == p
	})
}

// Classify 分類noごとにする。結果は分類noでソートされ、ListはSortOrderでソートされる
func (s SpotExpLevels) Classify() []*ClassifiedSpotExpLevels {
	grouped := slice.GroupBy(s, func(_ int, e *SpotExpLevel) (int, SpotExpLevel) {
		return e.ClassNo, *e
	})
	var ret []*ClassifiedSpotExpLevels
	for k, e := range grouped {
		ret = append(ret, &ClassifiedSpotExpLevels{
			ClassNo: k,
			List:    e,
		})
	}
	slices.SortFunc(ret, func(a, b *ClassifiedSpotExpLevels) int {
		return cmp.Compare(a.ClassNo, b.ClassNo)
	})
	for _, e := range ret {
		slices.SortFunc(e.List, func(a, b SpotExpLevel) int {
			return cmp.Compare(a.SortOrder, b.SortOrder)
		})
	}
	return ret
}

// ClassifiedSpotExpLevels 分類Noごとのスポット熟練度
type ClassifiedSpotExpLevels struct {
	ClassNo int
	List    []SpotExpLevel
}

// スポット熟練度パターン
const (
	SpotExpLevelPatternNone SpotExpLevelPattern = "none"
	SpotExpLevelPatternA    SpotExpLevelPattern = "a"
	SpotExpLevelPatternB    SpotExpLevelPattern = "b"
	SpotExpLevelPatternC    SpotExpLevelPattern = "c"
	SpotExpLevelPatternD    SpotExpLevelPattern = "d"
	SpotExpLevelPatternE    SpotExpLevelPattern = "e"
)
