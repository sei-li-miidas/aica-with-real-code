package dto

type JobTypesSelectionRequest struct {
	JobtypeNames []string `json:"JobtypeNames"`
}

type JobTypeSearchFilterRequest struct {
	JobtypeName string `json:"JobtypeName" query:"JobtypeName"`
}
