package master

import (
	"database/sql/driver"

	"github.com/samber/lo"

	"aica/api/sdk/gormio/serializer"
	"aica/api/sdk/vo"
)

type (
	IndustryMiddleID int16

	// IndustryMiddle 業種中分類
	IndustryMiddle struct {
		ID              IndustryMiddleID // ID
		IndustryLargeID IndustryLargeID  // 業種大分類ID
		Name            string           // 名前
		SortOrder       int
	}

	IndustryMiddles   list[IndustryMiddleID, IndustryMiddle]
	IndustryMiddleMap Map[IndustryMiddleID, IndustryMiddle]
)

func (i IndustryMiddle) GetID() IndustryMiddleID {
	return i.ID
}

func (i IndustryMiddle) TableName() string {
	return "master.industry_middle"
}

// IndustryLargeID 業種小に紐づく業種大分類IDを取得
func (id IndustryMiddleID) IndustryLargeID() IndustryLargeID {
	return IndustryLargeID(id / 100)
}

func (id *IndustryMiddleID) Scan(value any) error {
	return serializer.JobIDScan(id, value)
}

func (id IndustryMiddleID) Value() (driver.Value, error) {
	return serializer.JobIDValue(id)
}

func (id *IndustryMiddleID) UnmarshalJSON(value []byte) error {
	return serializer.JobIDUnmarshalJSON(id, value)
}

func (id IndustryMiddleID) MarshalJSON() ([]byte, error) {
	return serializer.JobIDMarshalJSON(id)
}

func (im IndustryMiddles) ToMap() IndustryMiddleMap {
	return IndustryMiddleMap(list[IndustryMiddleID, IndustryMiddle](im).ToMap())
}

func (im IndustryMiddles) Filter(condition func(e *IndustryMiddle) bool) IndustryMiddles {
	return list[IndustryMiddleID, IndustryMiddle](im).Filter(condition)
}

func (im IndustryMiddleMap) Get(id IndustryMiddleID) (*IndustryMiddle, bool) {
	return Map[IndustryMiddleID, IndustryMiddle](im).Get(id)
}

func (im IndustryMiddleMap) IDNamePairs(ids []IndustryMiddleID) []vo.IDNamePair[IndustryMiddleID] {
	return lo.Map(ids, func(id IndustryMiddleID, _ int) vo.IDNamePair[IndustryMiddleID] {
		name := ""
		if j, found := im[id]; found {
			name = j.Name
		}
		return *vo.NewIDNamePair(id, name)
	})
}
