package business

import (
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/business"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
)

type readPositionRepository interface {
	GetBusinessID(id position.ID) (*business.ID, error)
}

type readBusinessRepository interface {
	Get(id business.ID) (*business.Business, error)
}

type readCompanyRepository interface {
	Get(id company.ID) (*company.Company, error)
}

type industrySmallNameProvider interface {
	GetIndustrySmallNameIncludingAllIndustry(smallID master.IndustrySmallID) string
}
