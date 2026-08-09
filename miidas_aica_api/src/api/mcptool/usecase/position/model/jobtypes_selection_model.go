package model

import jobfilter "aica/api/domain/jobfilter"

type JobTypesSelection struct {
	JobtypeNames []string
}

type JobTypesSelectionResult struct {
	ToolName string
}

type JobTypeSearchFilter struct {
	SearchFilter *jobfilter.JobSearchFilter
	ToolName     string
}

type JobTypeSearchFilterQuery struct {
	JobtypeName string
}
