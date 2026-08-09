package master

import (
	"aica/api/sdk/vo"
)

type (
	EmployeeQtyID int

	// EmployeeQty 従業員数
	EmployeeQty struct {
		ID        EmployeeQtyID // ID
		Name      string        // 名前
		NumMin    int           // 下限
		NumMax    int           // 上限
		SortOrder int
	}

	EmployeeQtys = list[EmployeeQtyID, EmployeeQty]

	EmployeeQtyMap = Map[EmployeeQtyID, EmployeeQty]
)

func (e EmployeeQty) TableName() string {
	return "master.employee_qty"
}

func (e EmployeeQty) IDNamePair() *vo.IDNamePair[EmployeeQtyID] {
	return vo.NewIDNamePair(e.ID, e.Name)
}

func (e EmployeeQty) GetID() EmployeeQtyID {
	return e.ID
}
