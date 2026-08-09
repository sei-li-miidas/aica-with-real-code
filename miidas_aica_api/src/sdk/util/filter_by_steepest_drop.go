package util

import (
	"errors"
)

// DefaultMinGap 除外するために必要な最小ギャップサイズ
const DefaultMinGap = 0.1

// FilterBySteepestDrop はエルボー法（最大ギャップ）を適用します。
// results: distanceFuncで返される値でソート済み（昇順）である必要があります。
// minGap: 除外するために必要な最小ギャップサイズ（例：0.05または0.1）。
//
//	0.0より大きく1.0より小さい必要があります。
//
// distanceFunc: 各要素からdistance値を取得する関数。
func FilterBySteepestDrop[T any](results []T, minGap float64, distanceFunc func(T) float64) ([]T, error) {
	// バリデーション：minGapは0.0より大きく、1.0より小さい必要があります
	if minGap <= 0.0 {
		return nil, errors.New("minGapは0.0より大きい数字である必要があります")
	}
	if minGap >= 1.0 {
		return nil, errors.New("minGapは1.0より小さい数字である必要があります")
	}

	// 1. エッジケース：比較するデータが不足しています
	if len(results) < 2 {
		return results, nil
	}

	maxDiff := 0.0
	// 有意なギャップが見つからない場合は、デフォルトですべての結果を返します
	cutoffIndex := len(results) - 1

	// 2. 結果を反復処理して、最大の跳躍を見つけます
	for i := 0; i < len(results)-1; i++ {
		diff := distanceFunc(results[i+1]) - distanceFunc(results[i])

		// これまでに見つかった最大の差を追跡します。
		// 2つのギャップが同一である場合は >= を使って*早期*のカットを優先するか、
		// > を使って*後期*のカット（より多くの結果を保持）を優先します。
		// 通常は、> の方がより多くのコンテキストを保持するのに安全です。
		if diff > maxDiff {
			maxDiff = diff
			cutoffIndex = i
		}
	}

	// 3. 感度チェック
	// 「最大の跳躍」がごくわずかなノイズ（例：0.001）である場合、
	// リストをカットしてはいけません。すべてを返します。
	if maxDiff < minGap {
		return results, nil
	}

	// 4. カットオフまでのスライスを返します
	// cutoffIndexは跳躍*前*の要素のインデックスです。
	// Goのスライスでは、上限は排他的なので、cutoffIndex + 1を使用します。
	return results[:cutoffIndex+1], nil
}
