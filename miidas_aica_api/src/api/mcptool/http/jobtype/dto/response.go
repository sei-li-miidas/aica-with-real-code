package dto

import djobtype "aica/api/domain/jobtype"

type SearchSemanticJobTypeResponse struct {
	Keyword  string                          `json:"Keyword"`
	Jobtypes []*djobtype.JobTypeSearchResult `json:"Jobtypes"`
}
