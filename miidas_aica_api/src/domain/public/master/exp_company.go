package master

import (
	"aica/api/sdk/vo"
)

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=ExpCompanyID
type (
	ExpCompanyID int

	// ExpCompany 経験社数
	ExpCompany struct {
		ID        ExpCompanyID // ID
		Name      string       // 名前
		SortOrder int
	}

	ExpCompanies  = list[ExpCompanyID, ExpCompany]
	ExpCompanyMap = Map[ExpCompanyID, ExpCompany]
)

func (e ExpCompany) TableName() string {
	return "master.exp_company"
}

func (e ExpCompany) IDNamePair() *vo.IDNamePair[ExpCompanyID] {
	return vo.NewIDNamePair(e.ID, e.Name)
}

func (e ExpCompany) GetID() ExpCompanyID {
	return e.ID
}

const (
	ExpCompanyIDUnknown  ExpCompanyID = 0 // 経験企業数未入力
	ExpCompanyIDZero     ExpCompanyID = 1 // 経験企業数が0
	ExpCompanyID1        ExpCompanyID = 2
	ExpCompanyID2        ExpCompanyID = 3
	ExpCompanyID3        ExpCompanyID = 4
	ExpCompanyID4        ExpCompanyID = 5
	ExpCompanyID5        ExpCompanyID = 6
	ExpCompanyID6        ExpCompanyID = 7
	ExpCompanyID7        ExpCompanyID = 8
	ExpCompanyID8        ExpCompanyID = 9
	ExpCompanyID9        ExpCompanyID = 10
	ExpCompanyID10OrMore ExpCompanyID = 11
)

func (ex *ExpCompanyID) IsNone() bool {
	if ex == nil {
		return true
	}
	return *ex == ExpCompanyIDUnknown || *ex == ExpCompanyIDZero
}

// IsGreaterThan2ExpCompany 経験社数が2社よりも多いか判定
func (ex *ExpCompanyID) IsGreaterThan2ExpCompany() bool {
	if ex == nil {
		return false
	}
	return *ex > ExpCompanyID2
}
