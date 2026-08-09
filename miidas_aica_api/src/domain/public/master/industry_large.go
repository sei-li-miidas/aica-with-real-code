package master

import (
	"database/sql/driver"

	"github.com/samber/lo"

	"aica/api/sdk/gormio/serializer"
	"aica/api/sdk/vo"
)

type (
	IndustryLargeID int16

	// IndustryLarge 業種大分類
	IndustryLarge struct {
		ID        IndustryLargeID // ID
		Name      string          // 名前
		SortOrder int
	}
	IndustryLarges   list[IndustryLargeID, IndustryLarge]
	IndustryLargeMap Map[IndustryLargeID, IndustryLarge]
)

func (i IndustryLarge) GetID() IndustryLargeID {
	return i.ID
}

func (i IndustryLarge) TableName() string {
	return "master.industry_large"
}

func (id *IndustryLargeID) Scan(value any) error {
	return serializer.JobIDScan(id, value)
}

func (id IndustryLargeID) Value() (driver.Value, error) {
	return serializer.JobIDValue(id)
}

func (id *IndustryLargeID) UnmarshalJSON(value []byte) error {
	return serializer.JobIDUnmarshalJSON(id, value)
}

func (id IndustryLargeID) MarshalJSON() ([]byte, error) {
	return serializer.JobIDMarshalJSON(id)
}

func (im IndustryLarges) ToMap() IndustryLargeMap {
	return IndustryLargeMap(list[IndustryLargeID, IndustryLarge](im).ToMap())
}

func (im IndustryLargeMap) Get(id IndustryLargeID) (*IndustryLarge, bool) {
	return Map[IndustryLargeID, IndustryLarge](im).Get(id)
}

func (im IndustryLargeMap) IDNamePairs(ids []IndustryLargeID) []vo.IDNamePair[IndustryLargeID] {
	return lo.Map(ids, func(id IndustryLargeID, _ int) vo.IDNamePair[IndustryLargeID] {
		name := ""
		if j, found := im[id]; found {
			name = j.Name
		}
		return *vo.NewIDNamePair(id, name)
	})
}
