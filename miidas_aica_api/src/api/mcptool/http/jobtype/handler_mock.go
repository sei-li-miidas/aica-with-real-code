//go:build mock

package jobtype

import (
	dto "aica/api/api/mcptool/http/jobtype/dto"
	"aica/api/api/mcptool/http/mockutil"
	djobtype "aica/api/domain/jobtype"
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

func (h *MockHandler) searchSemanticJobType(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[*dto.SearchSemanticJobTypeResponse](mockData, "mockdata/search_semantic_jobtype.json"))
}

func (h *MockHandler) searchJobTypeByNature(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[[]*djobtype.JobTypeSearchResult](mockData, "mockdata/search_nature_jobtype.json"))
}

func (h *MockHandler) searchJobTypeByNames(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[[]*djobtype.JobTypeSearchResult](mockData, "mockdata/search_names_jobtype.json"))
}
