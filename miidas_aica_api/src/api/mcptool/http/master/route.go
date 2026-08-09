package master

import (
	dto "aica/api/api/mcptool/http/master/dto"
	mecho "aica/api/sdk/echo"
	mm "aica/api/sdk/echo/middleware"
	"fmt"
)

func Setup(e mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("master module handler is nil")
	}
	// 全部
	e.GET("/masters/", h.masters, mm.Binder(dto.GetMastersRequest{}).Build())
	return nil
}
