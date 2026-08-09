package vo

// 後日型名から Pair を削除する。

import (
	"strconv"

	"github.com/go-jose/go-jose/v4/json"
	"golang.org/x/exp/constraints"
)

type (
	// IntIDAndName IntIDNamePair を作るメソッドを提供するインタフェース
	IntIDAndName interface {
		IntIDNamePair() *IntIDNamePair
	}
)

// IDNamePair int likeのIDと名前のペア
type IDNamePair[I constraints.Integer] struct {
	ID   I
	Name string
}

// NewIDNamePair コンストラクタ
func NewIDNamePair[I constraints.Integer](id I, name string) *IDNamePair[I] {
	return &IDNamePair[I]{
		ID:   id,
		Name: name,
	}
}

// StrIDNamePair StrIDNamePairstringのIDと名前のペア
// Deprecated:
type StrIDNamePair struct {
	ID   string
	Name string
}

// NewStrIDNamePair コンストラクタ
// Deprecated:
func NewStrIDNamePair(id string, name string) *StrIDNamePair {
	return &StrIDNamePair{
		ID:   id,
		Name: name,
	}
}

type IDNamePairs[I constraints.Integer] []IDNamePair[I]

// IDs id だけの配列を取得
func (ps IDNamePairs[I]) IDs() []I {
	ret := make([]I, 0, len(ps))
	for _, v := range ps {
		ret = append(ret, v.ID)
	}
	return ret
}

// Names name だけの配列を取得
func (ps IDNamePairs[I]) Names() []string {
	ret := make([]string, 0, len(ps))
	for _, v := range ps {
		ret = append(ret, v.Name)
	}
	return ret
}

// ToMap id, name のマップに変換
func (ps IDNamePairs[I]) ToMap() map[I]IDNamePair[I] {
	ret := make(map[I]IDNamePair[I], len(ps))
	for _, v := range ps {
		ret[v.ID] = v
	}
	return ret
}

// 移行用エイリアス （後日 Deprecated にする）
type (
	// Deprecated:
	IntIDNamePair = IDNamePair[int]

	// Deprecated:
	IntIDNamePairs = IDNamePairs[int]
)

// NewIntIDNamePair コンストラクタ
// Deprecated:
func NewIntIDNamePair[I constraints.Integer](id I, name string) *IDNamePair[int] {
	return NewIDNamePair(int(id), name)
}

// IDNameChildPair int likeのIDと名前のペア（階層化可能）
type IDNameChildPair[I constraints.Integer] struct {
	ID       I
	Name     string
	Children []IDNameChildPair[I]
}

type IntIDNameChildPair = IDNameChildPair[int]

// jsonデータ内に ID が文字列だったものがあるのでその互換用構造体
type NumberIDNamePair[I constraints.Integer] IDNamePair[I]

func NewNumberIDNamePair[I constraints.Integer](id I, name string) *NumberIDNamePair[I] {
	return &NumberIDNamePair[I]{ID: id, Name: name}
}

func (p NumberIDNamePair[I]) IDNamePair() IDNamePair[I] {
	return IDNamePair[I](p)
}

// MarshalJSON 互換性維持のため、IDは文字列に変換する
func (p NumberIDNamePair[I]) MarshalJSON() ([]byte, error) {
	s := struct {
		ID   string
		Name string
	}{
		ID:   strconv.Itoa(int(p.ID)),
		Name: p.Name,
	}

	return json.Marshal(s)
}

func (p *NumberIDNamePair[I]) UnmarshalJSON(value []byte) error {
	var s struct {
		ID   json.Number
		Name string
	}
	if err := json.Unmarshal(value, &s); err != nil {
		return err
	}

	id, err := s.ID.Int64()
	if err != nil {
		return err
	}

	p.ID = I(id)
	p.Name = s.Name
	return nil
}

func (p IDNamePair[I]) NumberIDNamePair() *NumberIDNamePair[I] {
	return NewNumberIDNamePair(p.ID, p.Name)
}
