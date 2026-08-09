package vo

import (
	"github.com/samber/lo"
)

// ValueText 選択肢１つと補足テキスト
type ValueText struct {
	ID   int
	Text string `json:",omitempty"`
}

type ValueTexts []*ValueText

func NewValueText(id int, label string, text string) *ValueText {
	return &ValueText{
		ID:   id,
		Text: text,
	}
}

func (vt *ValueText) Init() *ValueText {
	if vt != nil {
		return vt
	}
	return &ValueText{}
}

func (vt *ValueText) GetIntPtr() *int {
	if vt == nil {
		return nil
	}
	return &vt.ID
}

// Flag ラベル付きフラグ
type Flag struct {
	On bool
}

func (f *Flag) Init() *Flag {
	if f != nil {
		return f
	}
	return &Flag{}
}

// TurnOn onにする
func (f *Flag) TurnOn() {
	f.On = true
}

// TurnOff offにする
func (f *Flag) TurnOff() {
	f.On = false
}

// FlagText フラグとテキスト
type FlagText struct {
	Flg  *Flag
	Text string `json:",omitempty"`
}

func (ft *FlagText) Init() *FlagText {
	if ft != nil {
		return ft
	}
	return &FlagText{
		Flg: &Flag{},
	}
}

// GetIntPtr TODO いけてない
func (ft *FlagText) GetIntPtr() *int {
	if ft == nil || ft.Flg == nil {
		return nil
	}
	if ft.Flg.On {
		return lo.ToPtr(1)
	}
	return lo.ToPtr(0)
}

// willのvalueとマッチしているかを返す
func (ft *FlagText) MatchWillValue(w int) bool {
	if ft == nil || ft.Flg == nil {
		return false
	}
	switch w {
	case 1:
		return ft.Flg.On
	case 2:
		return !ft.Flg.On
	}
	return false
}

// IDOnly IDだけの構造体
// Deprecated: 新規で使うのは禁止
type IDOnly struct {
	ID int
}

// IDOnlyList IDOnlyのリスト
type IDOnlyList []*IDOnly

// AppendID idの追加
func (l *IDOnlyList) AppendID(id int) {
	*l = append(*l, &IDOnly{ID: id})
}

// ToIntSlice []intに変換
func (l *IDOnlyList) ToIntSlice() []int {
	if l == nil {
		return nil
	}
	ret := make([]int, 0, len(*l))
	for _, idOnly := range *l {
		ret = append(ret, idOnly.ID)
	}
	return ret
}

// ValuesText 複数のIDとテキスト
type ValuesText struct {
	IDs  IDOnlyList
	Text string `json:",omitempty"`
}

func (vt *ValuesText) Init() *ValuesText {
	if vt != nil {
		return vt
	}
	return &ValuesText{}
}

func (vt *ValuesText) AppendID(id int) {
	vt.IDs = append(vt.IDs, &IDOnly{ID: id})
}

func (vt *ValuesText) GetIntIDs() []int {
	if vt == nil || len(vt.IDs) == 0 {
		return nil
	}
	ids := make([]int, 0, len(vt.IDs))
	for _, idWithName := range vt.IDs {
		ids = append(ids, idWithName.ID)
	}
	return ids
}

func (vt *ValueTexts) GetIntIDs() []int {
	if vt == nil || len(*vt) == 0 {
		return nil
	}
	ret := make([]int, 0, len(*vt))
	for _, idWithName := range *vt {
		ret = append(ret, idWithName.ID)
	}
	return ret
}
