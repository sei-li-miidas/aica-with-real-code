package position

import (
	positionDTO "aica/api/api/mcptool/http/position/dto"
	mecho "aica/api/sdk/echo"
	mm "aica/api/sdk/echo/middleware"
	"fmt"
)

func Setup(e mecho.RouteRegister, module *Module) error {
	h := module.Handler()
	if h == nil {
		return fmt.Errorf("position module handler is nil")
	}

	e.POST("/positions/search", h.search)
	e.POST("/positions/search/jobtype_specific", h.searchJobTypeSpecific)
	e.POST("/positions/search/it_engineer", h.searchITEngineer, mm.Binder(positionDTO.ITEngineerSearchRequest{}).Build())
	e.POST("/positions/search/financial_sales", h.searchFinancialSales, mm.Binder(positionDTO.FinancialSalesSearchRequest{}).Build())
	e.POST("/positions/summaries", h.summaries, mm.Binder(positionDTO.PositionSummariesRequest{}).Build())
	e.POST("/positions/detail/:position_id", h.detail)
	e.GET("/positions/recommendations/:theme", h.recommendations)
	e.GET("/positions/recommendations/it_engineer/:theme", h.searchITEngineerTheme)
	e.GET("/positions/recommendations/financial_sales/:theme", h.searchFinancialSalesTheme)
	e.POST("/positions/jobtypes/decided", h.jobTypesSelected, mm.Binder(positionDTO.JobTypesSelectionRequest{}).Build())
	e.POST("/positions/jobtypes/clear", h.jobTypesClear)
	e.GET("/positions/search_filter/jobtype", h.jobTypeSearchFilter, mm.Binder(positionDTO.JobTypeSearchFilterRequest{}).Build())
	e.GET("/positions/search_filter/current", h.currentJobTypeSearchFilter)
	return nil
}
