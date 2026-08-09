package location

import "github.com/labstack/echo/v4"

type routeHandler interface {
	verifyPrefectureCity(c echo.Context) error
	searchCommutingAreas(c echo.Context) error
	searchByKeyword(c echo.Context) error
}
