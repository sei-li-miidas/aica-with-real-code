package dto

import (
	address "aica/api/api/mcptool/usecase/shared"
	mposition "aica/api/domain/user/apply/position"
)

type PositionSearchCommonRequest struct {
	ToolName        string                     `json:"ToolName"`
	JobtypeNames    []string                   `json:"JobtypeNames"`
	Salary          int32                      `json:"Salary"`
	Locations       []*address.LocationRequest `json:"Locations"`
	PositionKeyword *string                    `json:"PositionKeyword"`

	// TODO: https://miidas-dev.slack.com/archives/C08CPHXCZ08/p1773133846012799?thread_ts=1769587226.569069&cid=C08CPHXCZ08
	DayOffs         *[]string `json:"DayOffs"`
	AverageOvertime *string   `json:"AverageOvertime"`
}

type PositionSearchRequest struct {
	PositionSearchCommonRequest
}

type ITEngineerSearchRequest struct {
	PositionSearchCommonRequest

	RemoteWorkPossible *bool `json:"RemoteWorkPossible"`

	ProgrammingLanguages    *[]string `json:"ProgrammingLanguages"`
	ProjectScales           *[]string `json:"ProjectScales"`
	ApplicationFrameworks   *[]string `json:"ApplicationFrameworks"`
	CloudServices           *[]string `json:"CloudServices"`
	Phases                  *[]string `json:"Phases"`
	Positions               *[]string `json:"Positions"`
	SystemScales            *[]string `json:"SystemScales"`
	DevelopmentProjectTypes *[]string `json:"DevelopmentProjectTypes"`
}

type FinancialSalesSearchRequest struct {
	PositionSearchCommonRequest

	HandledFinancialProducts *[]string `json:"HandledFinancialProducts"`
	SalesStyleDive           *string   `json:"SalesStyleDive"`
	SalesMethodStyles        *[]string `json:"SalesMethodStyles"`
	TargetCustomerTypes      *[]string `json:"TargetCustomerTypes"`

	Qualifications        *[]string `json:"Qualifications"`
	IndividualSalesStyles *[]string `json:"IndividualSalesStyles"`
	IncentiveSystem       *string   `json:"IncentiveSystem"`
}

type PositionSummariesRequest struct {
	PositionIDs []mposition.ID `json:"PositionIDs"`
}
