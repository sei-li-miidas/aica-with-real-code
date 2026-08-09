package company

import (
	mecho "aica/api/sdk/echo"
	"fmt"
)

func Setup(r mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("company module handler is nil")
	}
	r.GET("/companies/detail/position_id/:position_id", h.getDetail)
	return nil
}
