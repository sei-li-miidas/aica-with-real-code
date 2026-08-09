package mapper

import (
	dto "aica/api/api/mcptool/http/position/dto"
	pmodel "aica/api/api/mcptool/usecase/position/model"
)

func ToJobTypesSelectedRequest(req *dto.JobTypesSelectionRequest) *pmodel.JobTypesSelection {
	if req == nil {
		return nil
	}
	return &pmodel.JobTypesSelection{
		JobtypeNames: req.JobtypeNames,
	}
}

func ToJobTypeSearchFilterRequest(req *dto.JobTypeSearchFilterRequest) *pmodel.JobTypeSearchFilterQuery {
	if req == nil {
		return nil
	}
	return &pmodel.JobTypeSearchFilterQuery{
		JobtypeName: req.JobtypeName,
	}
}

func ToJobTypesSelectedResponse(result *pmodel.JobTypesSelectionResult) *dto.JobTypesSelectionResponse {
	if result == nil {
		return &dto.JobTypesSelectionResponse{}
	}
	return &dto.JobTypesSelectionResponse{ToolName: result.ToolName}
}
