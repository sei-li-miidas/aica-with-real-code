package business

import "github.com/labstack/echo/v4"

type routeHandler interface {
	getDetail(c echo.Context) error
}
