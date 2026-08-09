package position

import "github.com/labstack/echo/v4"

type routeHandler interface {
	search(c echo.Context) error
	searchJobTypeSpecific(c echo.Context) error
	searchITEngineer(c echo.Context) error
	searchFinancialSales(c echo.Context) error
	summaries(c echo.Context) error
	detail(c echo.Context) error
	recommendations(c echo.Context) error
	searchITEngineerTheme(c echo.Context) error
	searchFinancialSalesTheme(c echo.Context) error
	jobTypesSelected(c echo.Context) error
	jobTypesClear(c echo.Context) error
	jobTypeSearchFilter(c echo.Context) error
	currentJobTypeSearchFilter(c echo.Context) error
}
