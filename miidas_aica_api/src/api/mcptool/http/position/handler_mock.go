//go:build mock

package position

import (
	"aica/api/api/mcptool/http/mockutil"
	mPosition "aica/api/domain/user/apply/position"
	mecho "aica/api/sdk/echo"
	"embed"
	"net/http"

	"github.com/labstack/echo/v4"
)

type MockHandler struct{}

func newMockHandler() *MockHandler {
	return &MockHandler{}
}

//go:embed mockdata/*.json
var mockData embed.FS

func (m *MockHandler) search(c echo.Context) error {
	return c.JSON(http.StatusOK, withRecommendationThemePrefix(loadObject("mockdata/search_envelope.json"), "search/"))
}

func (m *MockHandler) searchJobTypeSpecific(c echo.Context) error {
	return c.JSON(http.StatusOK, withRecommendationThemePrefix(loadObject("mockdata/search_envelope.json"), "jobtype_specific/"))
}

func (m *MockHandler) searchITEngineer(c echo.Context) error {
	return c.JSON(http.StatusOK, withRecommendationThemePrefix(loadObject("mockdata/search_envelope.json"), "it_engineer/"))
}

func (m *MockHandler) searchFinancialSales(c echo.Context) error {
	return c.JSON(http.StatusOK, withRecommendationThemePrefix(loadObject("mockdata/search_envelope.json"), "financial_sales/"))
}

func (m *MockHandler) recommendations(c echo.Context) error {
	return c.JSON(http.StatusOK, loadObject("mockdata/search_envelope.json"))
}

func (m *MockHandler) searchITEngineerTheme(c echo.Context) error {
	return c.JSON(http.StatusOK, withRecommendationThemePrefix(loadObject("mockdata/search_envelope.json"), "it_engineer/"))
}

func (m *MockHandler) searchFinancialSalesTheme(c echo.Context) error {
	return c.JSON(http.StatusOK, withRecommendationThemePrefix(loadObject("mockdata/search_envelope.json"), "financial_sales/"))
}

func (m *MockHandler) summaries(c echo.Context) error {
	return c.JSON(http.StatusOK, loadObject("mockdata/summaries.json"))
}

func (m *MockHandler) detail(c echo.Context) error {
	id, err := mecho.GetFromParam[mPosition.ID](c, "position_id")
	if err != nil || id <= 0 {
		return echo.NewHTTPError(http.StatusBadRequest, "invalid position_id")
	}

	resp := loadObject("mockdata/detail.json")
	positionObj, ok := resp["Position"].(map[string]any)
	if ok {
		positionObj["ID"] = id
	}
	return c.JSON(http.StatusOK, resp)
}

func (m *MockHandler) jobTypesSelected(c echo.Context) error {
	return c.JSON(http.StatusOK, loadObject("mockdata/jobtypes_selected.json"))
}

func (m *MockHandler) jobTypesClear(c echo.Context) error {
	return c.JSON(http.StatusOK, loadObject("mockdata/jobtypes_clear.json"))
}

func (m *MockHandler) jobTypeSearchFilter(c echo.Context) error {
	return c.JSON(http.StatusOK, loadObject("mockdata/jobtype_search_filter.json"))
}

func (m *MockHandler) currentJobTypeSearchFilter(c echo.Context) error {
	if _, ok := c.QueryParams()["empty"]; ok {
		return c.JSON(http.StatusOK, loadObject("mockdata/current_jobtype_search_filter_empty.json"))
	}
	return c.JSON(http.StatusOK, loadObject("mockdata/current_jobtype_search_filter.json"))
}

func loadObject(path string) map[string]any {
	return mockutil.MustLoadJSON[map[string]any](mockData, path)
}

func withRecommendationThemePrefix(envelope map[string]any, prefix string) map[string]any {
	rawRecommendations, ok := envelope["Recommendations"].([]any)
	if !ok {
		return envelope
	}

	for _, item := range rawRecommendations {
		rec, ok := item.(map[string]any)
		if !ok {
			continue
		}
		theme, ok := rec["Theme"].(string)
		if !ok {
			continue
		}
		rec["Theme"] = prefix + theme
	}

	return envelope
}
