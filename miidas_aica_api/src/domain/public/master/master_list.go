package master

import (
	"github.com/samber/lo"
)

// TODO: Mapと含めて https://github.com/wk8/go-ordered-map に移行。

// list マスターのリスト
type list[K comparable, E IDHolder[K]] []*E

// ToMap listをIDをキーにしたmapにして返す。
func (l list[K, E]) ToMap() Map[K, E] {
	return lo.SliceToMap(l, func(e *E) (K, *E) {
		return (*e).GetID(), e
	})
}

// Find list を走査して、最初の condition() に合致したものを返す。該当なしの場合は nil
func (l list[K, E]) Find(condition func(e *E) bool) *E {
	for _, e := range l {
		if condition(e) {
			return e
		}
	}

	return nil
}

// Filter list を走査して、condition() に合致したものを返す
func (l list[K, E]) Filter(condition func(e *E) bool) []*E {
	ret := make([]*E, 0, len(l))
	for _, e := range l {
		if condition(e) {
			ret = append(ret, e)
		}
	}
	return ret
}
