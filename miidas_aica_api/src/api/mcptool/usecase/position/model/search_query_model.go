package model

import address "aica/api/api/mcptool/usecase/shared"

type CommonPositionSearchParams struct {
	JobtypeNames    []string
	Salary          int32
	Locations       []*address.LocationRequest
	DayOffs         *[]string
	AverageOvertime *string
}

type GenericPositionSearchParams struct {
	CommonPositionSearchParams

	PositionKeyword string
}

func (p *GenericPositionSearchParams) GetSalary() int32 {
	if p == nil {
		return 0
	}
	return p.Salary
}
