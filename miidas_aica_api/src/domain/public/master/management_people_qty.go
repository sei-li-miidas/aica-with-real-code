package master

import "aica/api/sdk/vo"

type (
	ManagementPeopleQtyID int

	// ManagementPeopleQty マネジメント経験人数
	ManagementPeopleQty struct {
		ID        ManagementPeopleQtyID // ID
		Name      string                // 名前
		QtyMin    int                   // 下限
		QtyMax    int                   // 上限
		SortOrder int
	}

	ManagementPeopleQtys   = list[ManagementPeopleQtyID, ManagementPeopleQty]
	ManagementPeopleQtyMap = Map[ManagementPeopleQtyID, ManagementPeopleQty]
)

func (m ManagementPeopleQty) TableName() string {
	return "master.management_people_qty"
}

func (m ManagementPeopleQty) IDNamePair() *vo.IDNamePair[ManagementPeopleQtyID] {
	return vo.NewIDNamePair(m.ID, m.Name)
}

func (m ManagementPeopleQty) GetID() ManagementPeopleQtyID {
	return m.ID
}

const (
	ManagementPeopleQtyID1To4      ManagementPeopleQtyID = 1 // 1〜4人
	ManagementPeopleQtyID5To9      ManagementPeopleQtyID = 2 // 5〜9人
	ManagementPeopleQtyID10To29    ManagementPeopleQtyID = 3 // 10〜29人
	ManagementPeopleQtyID30To99    ManagementPeopleQtyID = 4 // 30〜99人
	ManagementPeopleQtyID100OrMore ManagementPeopleQtyID = 5 // 100人以上
)
