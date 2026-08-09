package dto

type SearchSemanticJobTypeRequest struct {
	Keyword  string   `json:"Keyword"`
	Provider *string  `json:"Provider"`
	Distance *float64 `json:"Distance"`
	Limit    *uint    `json:"Limit"`
}

type SearchJobTypeByNatureRequest struct {
	JobNaturePreferences       []*JobNaturePreference `json:"JobNaturePreferences"`
	MinNatureScore             *float32               `json:"MinNatureScore"`
	MinJobTypeScore            *float32               `json:"MinJobTypeScore"`
	MaxPriorExperienceRequired *float32               `json:"MaxPriorExperienceRequired"`
}

type JobNaturePreference struct {
	JobNature  string `json:"JobNature"`
	Preference string `json:"Preference"`
}

type SearchJobTypesByNameRequest struct {
	Names []string `json:"Names"`
}
