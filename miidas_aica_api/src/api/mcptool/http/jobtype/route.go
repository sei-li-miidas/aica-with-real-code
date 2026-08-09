package jobtype

import (
	dto "aica/api/api/mcptool/http/jobtype/dto"
	mecho "aica/api/sdk/echo"
	mm "aica/api/sdk/echo/middleware"
	"fmt"
)

func Setup(e mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("jobtype module handler is nil")
	}
	e.POST("/jobtype/search/semantic", h.searchSemanticJobType, mm.Binder(dto.SearchSemanticJobTypeRequest{}).Build())
	e.POST("/jobtype/search/nature", h.searchJobTypeByNature, mm.Binder(dto.SearchJobTypeByNatureRequest{}).Build())
	e.POST("/jobtype/search/names", h.searchJobTypeByNames, mm.Binder(dto.SearchJobTypesByNameRequest{}).Build())
	return nil
}
