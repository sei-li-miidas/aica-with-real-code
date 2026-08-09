package master

import (
	"aica/api/sdk/vo"
)

// EmploymentType 雇用形態
type (
	EmploymentTypeID int
	EmploymentType   struct {
		ID        EmploymentTypeID // ID
		Name      string           // 名前
		JDFlg     bool             // 求人使用可能フラグ
		SortOrder int
	}

	EmploymentTypes = list[EmploymentTypeID, EmploymentType]

	EmploymentTypeMap = Map[EmploymentTypeID, EmploymentType]
)

func (e EmploymentType) TableName() string {
	return "master.employment_type"
}

func (e EmploymentType) IDNamePair() *vo.IDNamePair[EmploymentTypeID] {
	return vo.NewIDNamePair(e.ID, e.Name)
}

func (e EmploymentType) GetID() EmploymentTypeID {
	return e.ID
}

func (e EmploymentType) GetName() string {
	return e.Name
}

const (
	EmploymentTypeIDEmployee    EmploymentTypeID = 1 // 正社員
	EmploymentTypeIDContract    EmploymentTypeID = 2 // 契約社員
	EmploymentTypeIDOfficer     EmploymentTypeID = 3 // 役員（任用契約）
	EmploymentTypeIDOutsourcing EmploymentTypeID = 4 // 業務委託
	EmploymentTypeIDTemporary   EmploymentTypeID = 5 // 派遣社員
	EmploymentTypeIDPartTime    EmploymentTypeID = 6 // アルバイト
	EmploymentTypeIDOther       EmploymentTypeID = 7 // その他
)
