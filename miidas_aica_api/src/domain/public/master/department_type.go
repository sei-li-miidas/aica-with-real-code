package master

import (
	"aica/api/sdk/vo"
)

type (
	DepartmentTypeID int

	// DepartmentType 学部区分
	DepartmentType struct {
		ID        DepartmentTypeID // ID
		Name      string           // 名前
		SortOrder int
	}

	DepartmentTypes   = list[DepartmentTypeID, DepartmentType]
	DepartmentTypeMap = Map[DepartmentTypeID, DepartmentType]
)

func (dt DepartmentType) TableName() string {
	return "master.department_type"
}

func (dt DepartmentType) IDNamePair() *vo.IDNamePair[DepartmentTypeID] {
	if dt.ID == 0 {
		return nil
	}
	return vo.NewIDNamePair(dt.ID, dt.Name)
}

func (dt DepartmentType) GetID() DepartmentTypeID {
	return dt.ID
}
