package industry

import (
	dto "aica/api/api/mcptool/http/industry/dto"
	dindustry "aica/api/domain/industry"
	mectx "aica/api/sdk/echo/context"
	mhttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

func TestSearchSemanticIndustry_EmptySentence_ReturnsBadRequest(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/industry/search/semantic", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, &dto.SearchSemanticIndustryRequest{})

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticIndustryUseCase {
			return &stubSemanticSearcher{execute: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*dindustry.IndustrySearchResult, error) {
				return nil, nil
			}}
		},
	)
	err := h.searchSemanticIndustry(c)
	assert.NoError(t, err)
	assert.Equal(t, http.StatusBadRequest, rec.Code)
}
