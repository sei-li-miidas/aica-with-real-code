package util

import (
	"testing"
)

type testSearchResult struct {
	ID       int
	Distance float64
}

func TestFilterBySteepestDrop(t *testing.T) {
	tests := []struct {
		name           string
		results        []*testSearchResult
		minGap         float64
		expectedLength int
		description    string
	}{
		{
			name:        "クラスタリング近ゼロ（最大ギャップあり）",
			description: "ゼロ付近にクラスタリングされ、その後大きなギャップがあるデータ",
			results: searchResultsWithDistances([]float64{
				0.01, 0.02, 0.03, 0.05, 0.08,
				0.25, 0.30, 0.35, 0.40, 0.45,
			}),
			minGap:         0.1,
			expectedLength: 5,
		},
		{
			name:        "クラスタリング0.5付近（最大ギャップあり）",
			description: "0.5付近にクラスタリングされ、その後大きなギャップがあるデータ",
			results: searchResultsWithDistances([]float64{
				0.45, 0.48, 0.50, 0.52, 0.55,
				0.80, 0.85, 0.90, 0.95, 1.00,
			}),
			minGap:         0.2,
			expectedLength: 5,
		},
		{
			name:        "クラスタリング1.0付近（最大ギャップあり）",
			description: "1.0付近にクラスタリングされ、その後大きなギャップがあるデータ",
			results: searchResultsWithDistances([]float64{
				0.95, 0.98, 1.00, 1.02, 1.05,
				1.50, 1.55, 1.60, 1.65, 1.70,
			}),
			minGap:         0.4,
			expectedLength: 5,
		},
		{
			name:        "非常にタイト（ギャップなし）",
			description: "すべての値が非常に近く、大きなギャップがないデータ",
			results: searchResultsWithDistances([]float64{
				0.10, 0.101, 0.102, 0.103, 0.104,
				0.105, 0.106, 0.107, 0.108, 0.109,
			}),
			minGap:         0.1,
			expectedLength: 10,
		},
		{
			name:        "広く分散（複数の候補ギャップ）",
			description: "広い範囲に分散し、複数の潜在的なギャップがあるデータ",
			results: searchResultsWithDistances([]float64{
				0.05, 0.10, 0.15, 0.20, 0.25,
				0.50, 0.75, 1.00, 1.25, 1.50,
			}),
			minGap:         0.2,
			expectedLength: 5,
		},
		{
			name:        "2つのクラスタ（明確なギャップ）",
			description: "2つのクラスタが明確に分離されているデータ",
			results: searchResultsWithDistances([]float64{
				0.01, 0.02, 0.03, 0.04, 0.05,
				0.50, 0.51, 0.52, 0.53, 0.54,
			}),
			minGap:         0.3,
			expectedLength: 5,
		},
		{
			name:        "3つのクラスタ（最大ギャップを選択）",
			description: "3つのクラスタがあり、最大のギャップを見つけるデータ",
			results: searchResultsWithDistances([]float64{
				0.05, 0.06, 0.07, 0.08, 0.09,
				0.30, 0.31, 0.32, 0.33, 0.34,
				0.70, 0.71, 0.72, 0.73, 0.74,
			}),
			minGap:         0.15,
			expectedLength: 10,
		},
		{
			name:        "エッジケース：2つ未満の結果",
			description: "データが1つ以下の場合",
			results: searchResultsWithDistances([]float64{
				0.05,
			}),
			minGap:         0.1,
			expectedLength: 1,
		},
		{
			name:           "エッジケース：空の結果",
			description:    "データが空の場合",
			results:        searchResultsWithDistances([]float64{}),
			minGap:         0.1,
			expectedLength: 0,
		},
		{
			name:        "非常に大きなminGap（何もカットされない）",
			description: "minGapが非常に大きく、ギャップが最小値以下の場合",
			results: searchResultsWithDistances([]float64{
				0.05, 0.10, 0.15, 0.20, 0.25,
				0.30, 0.35, 0.40, 0.45, 0.50,
			}),
			minGap:         0.99,
			expectedLength: 10,
		},
		{
			name:        "グラデュアルな増加（ギャップなし）",
			description: "徐々に増加するデータで、大きなギャップがない",
			results: searchResultsWithDistances([]float64{
				0.1, 0.2, 0.3, 0.4, 0.5,
				0.6, 0.7, 0.8, 0.9, 1.0,
			}),
			minGap:         0.05,
			expectedLength: 7,
		},
	}

	distanceFunc := func(r *testSearchResult) float64 { return r.Distance }

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := FilterBySteepestDrop(tt.results, tt.minGap, distanceFunc)
			if err != nil {
				t.Errorf("[%s] 予期しないエラー: %v", tt.name, err)
				return
			}

			if len(result) != tt.expectedLength {
				t.Errorf(
					"[%s] 期待長: %d, 得られた長さ: %d\n説明: %s",
					tt.name, tt.expectedLength, len(result), tt.description,
				)
			}

			if len(result) > 0 && len(tt.results) > 0 {
				for i := 0; i < len(result); i++ {
					if result[i].Distance != tt.results[i].Distance {
						t.Errorf(
							"[%s] インデックス %d でのソート順が破損しています。期待: %f, 得られた: %f",
							tt.name, i, tt.results[i].Distance, result[i].Distance,
						)
					}
				}
			}
		})
	}
}

func searchResultsWithDistances(distances []float64) []*testSearchResult {
	results := make([]*testSearchResult, len(distances))
	for i, d := range distances {
		results[i] = &testSearchResult{
			ID:       i + 1,
			Distance: d,
		}
	}
	return results
}

func TestFilterBySteepestDropError(t *testing.T) {
	tests := []struct {
		name        string
		minGap      float64
		shouldError bool
	}{
		{
			name:        "minGap = 0.0（エラー）",
			minGap:      0.0,
			shouldError: true,
		},
		{
			name:        "minGap = -0.1（エラー）",
			minGap:      -0.1,
			shouldError: true,
		},
		{
			name:        "minGap = 1.0（エラー）",
			minGap:      1.0,
			shouldError: true,
		},
		{
			name:        "minGap = 1.5（エラー）",
			minGap:      1.5,
			shouldError: true,
		},
		{
			name:        "minGap = 0.1（有効）",
			minGap:      0.1,
			shouldError: false,
		},
		{
			name:        "minGap = 0.99（有効）",
			minGap:      0.99,
			shouldError: false,
		},
	}

	distanceFunc := func(r *testSearchResult) float64 { return r.Distance }

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			results := searchResultsWithDistances([]float64{
				0.1, 0.2, 0.3, 0.4, 0.5,
			})
			_, err := FilterBySteepestDrop(results, tt.minGap, distanceFunc)

			if tt.shouldError {
				if err == nil {
					t.Errorf("[%s] エラーが期待されましたが、発生しませんでした", tt.name)
				}
			} else {
				if err != nil {
					t.Errorf("[%s] エラーが予期されませんでしたが、発生しました: %v", tt.name, err)
				}
			}
		})
	}
}
