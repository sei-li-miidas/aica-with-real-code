package business

import (
	mecho "aica/api/sdk/echo"
	"fmt"
)

func Setup(r mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("business module handler is nil")
	}
	r.GET("/businesses/detail/position_id/:position_id", h.getDetail)
	return nil
}
