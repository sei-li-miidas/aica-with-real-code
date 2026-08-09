package master

import "github.com/labstack/echo/v4"

type routeHandler interface {
	masters(c echo.Context) error
}
