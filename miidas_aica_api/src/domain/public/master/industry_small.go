package master

import (
	"github.com/samber/lo"

	"aica/api/sdk/vo"
)

type (
	IndustrySmallID int32

	// IndustrySmall 業種小分類
	IndustrySmall struct {
		ID               IndustrySmallID  // ID
		IndustryMiddleID IndustryMiddleID // 業種中分類ID
		Name             string           // 名前
		SortOrder        int
	}

	IndustrySmalls   list[IndustrySmallID, IndustrySmall]
	IndustrySmallMap Map[IndustrySmallID, IndustrySmall]
)

func (i IndustrySmall) TableName() string {
	return "master.industry_small"
}

func (i IndustrySmall) IntIDNamePair() *vo.IntIDNamePair {
	return vo.NewIntIDNamePair(i.ID, i.Name)
}

func (i IndustrySmall) GetID() IndustrySmallID {
	return i.ID
}

const (
	AllIndustry     IndustrySmallID = 9000000 // すべての業種 B2Bの顧客の業種でのみ想定
	AllIndustryName                 = "すべての業種"
)

// IndustryLargeID 業種小に紐づく業種大分類IDを取得
func (i IndustrySmallID) IndustryLargeID() IndustryLargeID {
	return IndustryLargeID(i / 10000)
}

// IndustryMiddleID 業種小に紐づく業種中分類IDを取得
func (i IndustrySmallID) IndustryMiddleID() IndustryMiddleID {
	return IndustryMiddleID(i / 100)
}

func (im IndustrySmalls) ToMap() IndustrySmallMap {
	return IndustrySmallMap(list[IndustrySmallID, IndustrySmall](im).ToMap())
}

func (im IndustrySmalls) Filter(condition func(e *IndustrySmall) bool) IndustrySmalls {
	return list[IndustrySmallID, IndustrySmall](im).Filter(condition)
}

func (im IndustrySmallMap) Get(id IndustrySmallID) (*IndustrySmall, bool) {
	return Map[IndustrySmallID, IndustrySmall](im).Get(id)
}

func (im IndustrySmallMap) IDNamePairs(ids []IndustrySmallID) []vo.IDNamePair[IndustrySmallID] {
	return lo.Map(ids, func(id IndustrySmallID, _ int) vo.IDNamePair[IndustrySmallID] {
		name := ""
		if j, found := im[id]; found {
			name = j.Name
		}
		return *vo.NewIDNamePair(id, name)
	})
}
