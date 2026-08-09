package slice

// GroupBy スライスをキーでグループにしたマップ返す
//   - S:スライス要素
//   - K:キー
//   - V:マップの要素
//
// fには要素のindexと要素自身が渡されるので、キーとマップに入れたい要素を返してください。
func GroupBy[S any, K comparable, V any](s []S, f func(int, S) (K, V)) map[K][]V {
	ret := make(map[K][]V)
	for i, e := range s {
		k, v := f(i, e)
		ret[k] = append(ret[k], v)
	}
	return ret
}

// CountBy スライスの要素をキーを元にカウントし返す。
//   - S:スライス要素
//   - K:キー
//
// fには要素のindexと要素自身が渡されるので、キーを返してください。
func CountBy[S any, K comparable](s []S, f func(int, S) K) map[K]int {
	ret := make(map[K]int)
	for i, e := range s {
		g := f(i, e)
		ret[g]++
	}
	return ret
}

// Count スライスの要素をカウントする。
// isTargetがtrueを返したものをカウントします。
//   - S: スライスの要素
func Count[S any](s []S, isTarget func(int, S) bool) int {
	var ret int
	for i, e := range s {
		if isTarget(i, e) {
			ret++
		}
	}
	return ret
}

// Extract スライスから特定の要素のみを取り出したスライスを返す
//   - S:スライス要素
//   - V:取り出したい要素
//
// extractorには要素のindexと要素自身が渡されるので、取り出したい要素を返してください。
func Extract[S, V any](s []S, extractor func(int, S) V) []V {
	ret := make([]V, 0, len(s))
	for i, v := range s {
		ret = append(ret, extractor(i, v))
	}
	return ret
}

// Filter 条件に合う要素からなるスライスを返す
//   - S:スライス要素
func Filter[S any](s []S, isTarget func(int, S) bool) []S {
	ret := make([]S, 0, len(s))
	for i, e := range s {
		if isTarget(i, e) {
			ret = append(ret, e)
		}
	}
	return ret
}

// Find 条件に合う最初の要素を返す
//   - S:スライス要素
func Find[S any](s []S, isTarget func(S) bool) (S, bool) {
	for _, e := range s {
		if isTarget(e) {
			return e, true
		}
	}

	var ret S
	return ret, false
}

// Merge 複数のスライスを結合する
//   - S:スライス要素
func Merge[S any](ss ...[]S) []S {
	ret := make([]S, 0, SumLengths(ss))
	for _, e := range ss {
		ret = append(ret, e...)
	}
	return ret
}

// Total 複数のスライスに含まれる要素数の合計を返す
//   - S:スライス要素
func SumLengths[S any](ss ...[]S) int {
	var c int
	for _, e := range ss {
		c += len(e)
	}
	return c
}

// IsUnique スライスの要素がユニークかどうかを返す
//   - S:スライス要素
//
// 空スライスはユニークとみなす
func IsUnique[S comparable](s []S) bool {
	// 要素数0 または 1 なら
	if len(s) < 2 {
		return true
	}

	exists := make(map[S]struct{}, len(s))
	for i := range s {
		if _, ok := exists[s[i]]; ok {
			return false
		}
		exists[s[i]] = struct{}{}
	}

	return true
}
