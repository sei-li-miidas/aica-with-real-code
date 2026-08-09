package industry

import (
	"aica/api/sdk/logger"
	"net/http"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

func TestSetup_RegisterRoutes(t *testing.T) {
	e := echo.New()
	module, err := NewModule(Dependencies{
		NewSemanticUseCase: func(_ logger.LevelLogger) SemanticIndustryUseCase {
			return &stubSemanticSearcher{}
		},
	})
	assert.NoError(t, err)
	assert.NoError(t, Setup(e, module))

	hasRoute := false
	for _, r := range e.Routes() {
		if r.Method == http.MethodPost && r.Path == "/industry/search/semantic" {
			hasRoute = true
			break
		}
	}

	assert.True(t, hasRoute)
}
