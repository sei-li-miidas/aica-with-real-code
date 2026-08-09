package mapper

import (
	dto "aica/api/api/mcptool/http/position/dto"
	pmodel "aica/api/api/mcptool/usecase/position/model"
)

func ToDetailResponse(resp *pmodel.PositionDetail) *dto.PositionDetail {
	if resp == nil {
		return nil
	}
	return resp
}
