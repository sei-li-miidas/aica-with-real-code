package jobtype

import "github.com/labstack/echo/v4"

type routeHandler interface {
	searchSemanticJobType(c echo.Context) error
	searchJobTypeByNature(c echo.Context) error
	searchJobTypeByNames(c echo.Context) error
}
