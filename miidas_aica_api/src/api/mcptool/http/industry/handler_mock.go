//go:build mock

package industry

import (
	"aica/api/api/mcptool/http/mockutil"
	dindustry "aica/api/domain/industry"
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

func (h *MockHandler) searchSemanticIndustry(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[[]*dindustry.IndustrySearchResult](mockData, "mockdata/search_semantic_industry.json"))
}
