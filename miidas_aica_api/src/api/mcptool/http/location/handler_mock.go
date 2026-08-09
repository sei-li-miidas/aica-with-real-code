//go:build mock

package location

import (
	"aica/api/api/mcptool/http/mockutil"
	"embed"
	"net/http"

	"github.com/labstack/echo/v4"
)

type MockHandler struct{}

func NewMockHandler() *MockHandler {
	return &MockHandler{}
}

//go:embed mockdata/*.json
var mockData embed.FS

func (h *MockHandler) verifyPrefectureCity(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[[]map[string]any](mockData, "mockdata/verify_prefecture_city.json"))
}

func (h *MockHandler) searchCommutingAreas(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[[]map[string]any](mockData, "mockdata/search_commuting_areas.json"))
}

func (h *MockHandler) searchByKeyword(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[[]map[string]any](mockData, "mockdata/search_keyword.json"))
}
