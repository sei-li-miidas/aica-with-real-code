package dto

type JobTypeSearchFilterResponse struct {
	OtherFilters          []*JobSearchFilterOtherFilterResponse `json:"OtherFilters,omitempty"`
	SelectedFilterOptions map[string][]string                   `json:"SelectedFilterOptions,omitempty"`
}

type CurrentJobTypeSearchFilterResponse struct {
	ToolName                          string                   `json:"ToolName,omitempty"`
	SearchFilters                     *JobSearchFilterResponse `json:"SearchFilters,omitempty"`
	JobtypeNamesWithSameSearchFilters map[string][]string      `json:"JobtypeNamesWithSameSearchFilters,omitempty"`
}

type JobTypesSelectionResponse struct {
	ToolName string `json:"ToolName"`
}
