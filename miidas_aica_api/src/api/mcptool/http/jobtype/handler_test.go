package jobtype

import (
	dto "aica/api/api/mcptool/http/jobtype/dto"
	uc "aica/api/api/mcptool/usecase/jobtype"
	djobtype "aica/api/domain/jobtype"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	mhttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

func TestSearchSemanticJobType_EmptyKeyword_ReturnsBadRequest(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/jobtype/search/semantic", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, &dto.SearchSemanticJobTypeRequest{})

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{execute: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, nil
			}}
		},
		func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{execute: func(_ *uc.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, nil
			}}
		},
		func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{execute: func(_ []string) ([]*djobtype.JobTypeSmall, error) {
				return nil, nil
			}}
		},
	)
	err := h.searchSemanticJobType(c)
	assert.NoError(t, err)
	assert.Equal(t, http.StatusBadRequest, rec.Code)
}

func TestSearchSemanticJobType_BadParamType_ReturnsBadParameter(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/jobtype/search/semantic", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, "invalid")

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticJobTypeUseCase { return &stubSemanticSearcher{} },
		func(_ logger.LevelLogger) NatureJobTypeUseCase { return &stubNatureSearcher{} },
		func(_ logger.LevelLogger) NameJobTypeUseCase { return &stubNameSearcher{} },
	)
	assert.Equal(t, merr.ErrBadParameter, h.searchSemanticJobType(c))
}

func TestSearchJobTypeByNature_EmptyPreferences_ReturnsBadRequest(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/jobtype/search/nature", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, &dto.SearchJobTypeByNatureRequest{})

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{execute: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, nil
			}}
		},
		func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{execute: func(_ *uc.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, nil
			}}
		},
		func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{execute: func(_ []string) ([]*djobtype.JobTypeSmall, error) {
				return nil, nil
			}}
		},
	)
	err := h.searchJobTypeByNature(c)
	assert.NoError(t, err)
	assert.Equal(t, http.StatusBadRequest, rec.Code)
}

func TestSearchJobTypeByNature_BadParamType_ReturnsBadParameter(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/jobtype/search/nature", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, "invalid")

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticJobTypeUseCase { return &stubSemanticSearcher{} },
		func(_ logger.LevelLogger) NatureJobTypeUseCase { return &stubNatureSearcher{} },
		func(_ logger.LevelLogger) NameJobTypeUseCase { return &stubNameSearcher{} },
	)
	assert.Equal(t, merr.ErrBadParameter, h.searchJobTypeByNature(c))
}

func TestSearchJobTypeByNames_EmptyNames_ReturnsBadRequest(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/jobtype/search/names", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, &dto.SearchJobTypesByNameRequest{})

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{execute: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, nil
			}}
		},
		func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{execute: func(_ *uc.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, nil
			}}
		},
		func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{execute: func(_ []string) ([]*djobtype.JobTypeSmall, error) {
				return nil, nil
			}}
		},
	)
	err := h.searchJobTypeByNames(c)
	assert.NoError(t, err)
	assert.Equal(t, http.StatusBadRequest, rec.Code)
}

func TestSearchJobTypeByNames_BadParamType_ReturnsBadParameter(t *testing.T) {
	e := echo.New()
	req := httptest.NewRequest(http.MethodPost, "/jobtype/search/names", nil)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetBoundParam(c, "invalid")

	h := NewHandler(
		func(_ logger.LevelLogger) SemanticJobTypeUseCase { return &stubSemanticSearcher{} },
		func(_ logger.LevelLogger) NatureJobTypeUseCase { return &stubNatureSearcher{} },
		func(_ logger.LevelLogger) NameJobTypeUseCase { return &stubNameSearcher{} },
	)
	assert.Equal(t, merr.ErrBadParameter, h.searchJobTypeByNames(c))
}
