package industry

import (
	dto "aica/api/api/mcptool/http/industry/dto"
	mecho "aica/api/sdk/echo"
	mm "aica/api/sdk/echo/middleware"
	"fmt"
)

func Setup(e mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("industry module handler is nil")
	}
	e.POST("/industry/search/semantic", h.searchSemanticIndustry, mm.Binder(dto.SearchSemanticIndustryRequest{}).Build())
	return nil
}
