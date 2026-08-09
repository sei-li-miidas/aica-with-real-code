package company

import (
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/business"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
)

type readPositionRepository interface {
	GetCompanyID(id position.ID) (*company.ID, error)
}

type readCompanyRepository interface {
	Get(id company.ID) (*company.Company, error)
}

type readBusinessRepository interface {
	GetByCompanyID(companyID company.ID) ([]business.Business, error)
}

type prefectureProvider interface {
	PrefectureMap() master.PrefectureMap
}
