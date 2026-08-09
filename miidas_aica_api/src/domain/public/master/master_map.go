package master

import (
	mapset "github.com/deckarep/golang-set/v2"
)

// TODO: listと含めて https://github.com/wk8/go-ordered-map に移行。

// Map キー：I、要素：Eのポインタのマップ
type Map[I comparable, E any] map[I]*E

// Get 要素の取得
// 実行回数が少ない場合はsliceを走査するほうが高速です。
func (m Map[I, E]) Get(id I) (*E, bool) {
	return getFromMap(m, id)
}

// GetAll 複数の要素の取得
//   - idsに重複があっても一つ分しか返しません
//   - returnはidsの順番に並びます。
//   - 計算量：mapからの取得 * idsの要素数です。大量に取得する場合、sliceの走査より高速です。
func (m Map[I, E]) GetAll(ids ...I) []*E {
	return getAllFromMap(m, ids...)
}

func getFromMap[I comparable, E any](m map[I]E, id I) (E, bool) {
	v, found := m[id]
	return v, found
}

func getAllFromMap[I comparable, E any](m map[I]E, ids ...I) []E {
	done := mapset.NewThreadUnsafeSetWithSize[I](len(ids)) // idsが重複しているときにreturnする要素の重複を避けるため実行済みを保持しておく

	// TODO: ForEachOnce() のようなものを定義する + lo.FilterMap()
	ret := make([]E, 0, len(ids))
	for _, id := range ids {
		if done.ContainsOne(id) { // 実行済み
			continue
		}
		done.Add(id)
		if v, found := m[id]; found {
			ret = append(ret, v)
		}
	}
	return ret
}
