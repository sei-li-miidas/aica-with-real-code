package industry

import "github.com/labstack/echo/v4"

type routeHandler interface {
	searchSemanticIndustry(c echo.Context) error
}
