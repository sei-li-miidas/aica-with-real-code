package position

import (
	"net/http"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

func TestSetup_RegisterRoutes(t *testing.T) {
	e := echo.New()
	module := &Module{handler: NewHandler(HandlerDependencies{})}

	err := Setup(e, module)
	assert.NoError(t, err)

	expected := map[string]bool{
		"/positions/search":                  false,
		"/positions/search/jobtype_specific": false,
		"/positions/search/it_engineer":      false,
		"/positions/search/financial_sales":  false,
		"/positions/summaries":               false,
		"/positions/detail/:position_id":     false,
		"/positions/jobtypes/decided":        false,
		"/positions/jobtypes/clear":          false,
	}
	expectedGet := map[string]bool{
		"/positions/recommendations/:theme":                 false,
		"/positions/recommendations/it_engineer/:theme":     false,
		"/positions/recommendations/financial_sales/:theme": false,
		"/positions/search_filter/jobtype":                  false,
		"/positions/search_filter/current":                  false,
	}

	for _, r := range e.Routes() {
		if r.Method == http.MethodPost {
			if _, ok := expected[r.Path]; ok {
				expected[r.Path] = true
			}
		}
		if r.Method == http.MethodGet {
			if _, ok := expectedGet[r.Path]; ok {
				expectedGet[r.Path] = true
			}
		}
	}

	for path, found := range expected {
		assert.True(t, found, "route not registered: %s", path)
	}
	for path, found := range expectedGet {
		assert.True(t, found, "route not registered: %s", path)
	}
}
