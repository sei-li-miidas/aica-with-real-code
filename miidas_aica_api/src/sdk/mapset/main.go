package mapset

import (
	mapset "github.com/deckarep/golang-set/v2"
)

// Safe nil mapset を 空 mapset に変換する。
// mapset は値レシーバのメソッドしか定義されていないので nil safe ではない。
// 空 mapset に変換してメソッドチェーンを実行できるようにする。本家が nil safe 対応すれば不要。
func Safe[T comparable](s mapset.Set[T]) mapset.Set[T] {
	if s != nil {
		return s
	}
	return mapset.NewSet[T]()
}

// NewSetWithTransform スライスから変換関数による変換を行った結果で ThreadSafe Set を作成する
func NewSetWithTransform[T comparable, I any](is []I, transform func(I) T) mapset.Set[T] {
	set := mapset.NewSetWithSize[T](len(is))
	for _, i := range is {
		set.Add(transform(i))
	}
	return set
}

// NewSetWithFilterTransform スライスから変換・フィルタ関数による変換・フィルタを行った結果で ThreadSafe Set を作成する
func NewSetWithFilterTransform[T comparable, I any](is []I, transform func(I) (T, bool)) mapset.Set[T] {
	set := mapset.NewSetWithSize[T](len(is))
	for _, i := range is {
		ti, pick := transform(i)
		if pick {
			set.Add(ti)
		}
	}
	return set
}

// NewThreadUnsafeSetWithTransform スライスから変換関数による変換を行った結果で Un-ThreadSafe Set を作成する
func NewThreadUnsafeSetWithTransform[T comparable, I any](is []I, transform func(I) T) mapset.Set[T] {
	set := mapset.NewThreadUnsafeSetWithSize[T](len(is))
	for _, i := range is {
		set.Add(transform(i))
	}
	return set
}

// NewThreadUnsafeSetWithFilterTransform スライスから変換・フィルタ関数による変換・フィルタを行った結果で Un-ThreadSafe Set を作成する
func NewThreadUnsafeSetWithFilterTransform[T comparable, I any](is []I, transform func(I) (T, bool)) mapset.Set[T] {
	set := mapset.NewThreadUnsafeSetWithSize[T](len(is))
	for _, i := range is {
		ti, pick := transform(i)
		if pick {
			set.Add(ti)
		}
	}
	return set
}
