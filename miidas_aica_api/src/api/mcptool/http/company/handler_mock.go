//go:build mock

package company

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

func (h *MockHandler) getDetail(c echo.Context) error {
	resp := mockutil.MustLoadJSON[map[string]any](mockData, "mockdata/get_detail.json")
	resp["PositionID"] = c.Param("position_id")
	return c.JSON(http.StatusOK, resp)
}
