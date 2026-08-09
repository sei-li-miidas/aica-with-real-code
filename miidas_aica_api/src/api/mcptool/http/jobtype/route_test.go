package jobtype

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
		NewSemanticUseCase: func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{}
		},
		NewNatureUseCase: func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{}
		},
		NewNameUseCase: func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{}
		},
	})
	assert.NoError(t, err)
	assert.NoError(t, Setup(e, module))

	hasSemantic := false
	hasNature := false
	hasNames := false
	for _, r := range e.Routes() {
		if r.Method == http.MethodPost && r.Path == "/jobtype/search/semantic" {
			hasSemantic = true
		}
		if r.Method == http.MethodPost && r.Path == "/jobtype/search/nature" {
			hasNature = true
		}
		if r.Method == http.MethodPost && r.Path == "/jobtype/search/names" {
			hasNames = true
		}
	}

	assert.True(t, hasSemantic)
	assert.True(t, hasNature)
	assert.True(t, hasNames)
}
