package business

import (
	businessUC "aica/api/api/mcptool/usecase/business"
	"aica/api/domain/user/apply/position"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"errors"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

type stubGetDetailUseCase struct {
	execute func(positionID position.ID) (*businessUC.GetDetailResponse, error)
}

func (s *stubGetDetailUseCase) Execute(positionID position.ID) (*businessUC.GetDetailResponse, error) {
	return s.execute(positionID)
}

func TestNewModule(t *testing.T) {
	t.Run("error when usecase factory is nil", func(t *testing.T) {
		module, err := NewModule(Dependencies{})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new get detail usecase factory is required")
	})

	t.Run("success", func(t *testing.T) {
		module, err := NewModule(Dependencies{
			NewGetDetailUseCase: func(_ logger.LevelLogger) GetDetailUseCase {
				return &stubGetDetailUseCase{execute: func(position.ID) (*businessUC.GetDetailResponse, error) {
					return &businessUC.GetDetailResponse{}, nil
				}}
			},
		})
		assert.NoError(t, err)
		assert.NotNil(t, module)
		assert.NotNil(t, module.Handler())
	})
}

func TestModuleHandler_NilReceiver(t *testing.T) {
	var module *Module
	assert.Nil(t, module.Handler())
}

func TestSetup(t *testing.T) {
	t.Run("error when module is nil", func(t *testing.T) {
		e := echo.New()
		err := Setup(e, nil)
		assert.EqualError(t, err, "business module handler is nil")
	})

	t.Run("register route", func(t *testing.T) {
		e := echo.New()
		module, err := NewModule(Dependencies{
			NewGetDetailUseCase: func(_ logger.LevelLogger) GetDetailUseCase {
				return &stubGetDetailUseCase{execute: func(position.ID) (*businessUC.GetDetailResponse, error) {
					return &businessUC.GetDetailResponse{}, nil
				}}
			},
		})
		assert.NoError(t, err)
		assert.NoError(t, Setup(e, module))

		found := false
		for _, r := range e.Routes() {
			if r.Method == http.MethodGet && r.Path == "/businesses/detail/position_id/:position_id" {
				found = true
				break
			}
		}
		assert.True(t, found)
	})
}

func TestHandlerGetDetail(t *testing.T) {
	t.Run("invalid position_id", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/businesses/detail/position_id/abc", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		c.SetParamNames("position_id")
		c.SetParamValues("abc")

		h := NewHandler(func(_ logger.LevelLogger) GetDetailUseCase {
			return &stubGetDetailUseCase{}
		})
		err := h.getDetail(c)
		assert.Error(t, err)
		assert.True(t, merr.Is(err, merr.ErrInvalidRequest))
	})

	t.Run("usecase error", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/businesses/detail/position_id/1", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		c.SetParamNames("position_id")
		c.SetParamValues("1")

		h := NewHandler(func(_ logger.LevelLogger) GetDetailUseCase {
			return &stubGetDetailUseCase{
				execute: func(_ position.ID) (*businessUC.GetDetailResponse, error) {
					return nil, errors.New("usecase failed")
				},
			}
		})
		err := h.getDetail(c)
		assert.EqualError(t, err, "usecase failed")
	})

	t.Run("success", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodGet, "/businesses/detail/position_id/1", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		c.SetParamNames("position_id")
		c.SetParamValues("1")

		h := NewHandler(func(_ logger.LevelLogger) GetDetailUseCase {
			return &stubGetDetailUseCase{
				execute: func(_ position.ID) (*businessUC.GetDetailResponse, error) {
					return &businessUC.GetDetailResponse{}, nil
				},
			}
		})
		err := h.getDetail(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusOK, rec.Code)
		assert.True(t, strings.Contains(rec.Body.String(), "Business"))
	})
}
