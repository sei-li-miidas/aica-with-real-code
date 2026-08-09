//go:build mock

package master

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

func (h *MockHandler) masters(c echo.Context) error {
	return c.JSON(http.StatusOK, mockutil.MustLoadJSON[map[string]any](mockData, "mockdata/masters.json"))
}
