package location

import (
	dto "aica/api/api/mcptool/http/location/dto"
	mecho "aica/api/sdk/echo"
	mm "aica/api/sdk/echo/middleware"
	"fmt"
)

func Setup(e mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("location module handler is nil")
	}
	e.POST("/location/verify/prefecture/city", h.verifyPrefectureCity, mm.Binder(dto.VerifyPrefectureCityRequest{}).Build())
	e.POST("/location/search/commuting_areas", h.searchCommutingAreas, mm.Binder(dto.LocationRequest{}).Build())
	e.POST("/location/search/keyword", h.searchByKeyword, mm.Binder(dto.SearchByKeywordRequest{}).Build())
	return nil
}
