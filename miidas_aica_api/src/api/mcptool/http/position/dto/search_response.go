package dto

import (
	mposition "aica/api/domain/user/apply/position"
)

type SearchResponseEnvelope struct {
	AllPositionIds                    []mposition.ID                    `json:"AllPositionIds"`
	Positions                         []*PositionSummaryResponse        `json:"Positions"`
	Recommendations                   []*PositionRecommendationResponse `json:"Recommendations,omitempty"`
	SearchFilters                     *JobSearchFilterResponse          `json:"SearchFilters,omitempty"`
	JobtypeNamesWithSameSearchFilters map[string][]string               `json:"JobtypeNamesWithSameSearchFilters,omitempty"`
}

type PositionSummaryResponse struct {
	ID          mposition.ID `json:"ID"`
	Title       string       `json:"Title"`
	MainJobText string       `json:"MainJobText"`
	SalaryFrom  *int         `json:"SalaryFrom"`
	SalaryTo    *int         `json:"SalaryTo"`
	Image       string       `json:"Image"`
}

type PositionRecommendationResponse struct {
	Theme       string `json:"Theme"`
	Title       string `json:"Title"`
	Description string `json:"Description"`
}

type JobSearchFilterResponse struct {
	Jobtypes              map[string][]*JobSearchFilterJobtypeSelectableItemResponse `json:"Jobtypes"`
	Salary                int                                                        `json:"Salary"`
	Locations             *JobSearchFilterLocationsResponse                          `json:"Locations"`
	PositionKeyword       *string                                                    `json:"PositionKeyword"`
	OtherFilters          map[string][]*JobSearchFilterOtherFilterResponse           `json:"OtherFilters,omitempty"`
	SelectedFilterOptions map[string]map[string][]string                             `json:"SelectedFilterOptions,omitempty"`
}

type JobSearchFilterOtherFilterOptionResponse struct {
	Label string `json:"Label"`
	Value string `json:"Value"`
}

type JobSearchFilterJobtypeSelectableItemResponse struct {
	Label       string `json:"Label"`
	Value       string `json:"Value"`
	Description string `json:"Description"`
	Selected    bool   `json:"Selected"`
}

type JobSearchFilterLocationSelectableItemResponse struct {
	Label          string `json:"Label"`
	PrefectureName string `json:"PrefectureName"`
	CityName       string `json:"CityName"`
	Selected       bool   `json:"Selected"`
}

type JobSearchFilterResidenceResponse struct {
	Address        *JobSearchFilterAddressResponse                  `json:"Address,omitempty"`
	CommutingAreas []*JobSearchFilterLocationSelectableItemResponse `json:"CommutingAreas"`
}

type JobSearchFilterAddressResponse struct {
	PrefectureName string `json:"PrefectureName,omitempty"`
	CityName       string `json:"CityName,omitempty"`
}

type JobSearchFilterLocationsResponse struct {
	Residence          *JobSearchFilterResidenceResponse                `json:"Residence"`
	WorkLocations      []*JobSearchFilterLocationSelectableItemResponse `json:"WorkLocations"`
	RemoteWorkPossible *bool                                            `json:"RemoteWorkPossible"`
}

type JobSearchFilterOtherFilterResponse struct {
	Key     string                                      `json:"Key"`
	Name    string                                      `json:"Name"`
	Type    string                                      `json:"Type"`
	Options []*JobSearchFilterOtherFilterOptionResponse `json:"Options"`
}
