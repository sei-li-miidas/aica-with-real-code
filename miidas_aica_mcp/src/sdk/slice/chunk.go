package slice

type (
	// Indices はchunkを作るためのsliceの指定
	Indices struct {
		L int // Low
		H int // High
	}
)

// Size Indicesで取得できるsliceの大きさ
func (i *Indices) Size() int {
	if i == nil || (i.L == 0 && i.H == 0) {
		return 0
	}
	return i.H - i.L
}

// ChunkingIndex はchunkを作るために指定するLow/Highのペアを返します。
// 安全にできています。
func ChunkingIndex(totalLength, chunkingSize int) []Indices {
	if totalLength <= 0 { // sliceが空なのでchunking不要
		return []Indices{}
	}
	if chunkingSize <= 0 { // チャンクするサイズが0なので一つ
		return []Indices{
			{0, totalLength},
		}
	}

	if totalLength < chunkingSize {
		return []Indices{
			{0, totalLength},
		}
	}

	var result = []Indices{}
	for i := 0; i < totalLength; i += chunkingSize {
		if i+chunkingSize <= totalLength {
			result = append(result, Indices{i, i + chunkingSize})
		} else {
			result = append(result, Indices{i, totalLength})
		}
	}
	return result
}

// Index スライスに対してのoffset/limitです。
// 返されたIndicesを使うと安全に要素を取り出せます。
func Index(totalLength, offset, limit int) Indices {
	if totalLength <= 0 {
		return Indices{}
	}

	var result = Indices{}

	if offset > 0 {
		result.L = offset
	}
	if result.L > totalLength {
		result.L = totalLength // totalLengthを超えたindexは指定できないため切り詰める
	}

	if limit > 0 {
		result.H = result.L + limit
	} else {
		result.H = totalLength
	}
	if result.H > totalLength {
		result.H = totalLength // totalLengthを超えたindexは指定できないため切り詰める
	}

	return result
}
