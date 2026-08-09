package industry

import (
	dto "aica/api/api/mcptool/http/industry/dto"
	dindustry "aica/api/domain/industry"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	mhttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

type stubLevelLogger struct{}

func (l *stubLevelLogger) Info(string, ...any)  {}
func (l *stubLevelLogger) Warn(string, ...any)  {}
func (l *stubLevelLogger) Error(string, ...any) {}
func (l *stubLevelLogger) Fatal(string, ...any) {}

type stubSemanticSearcher struct {
	execute func(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*dindustry.IndustrySearchResult, error)
}

func (s *stubSemanticSearcher) Execute(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*dindustry.IndustrySearchResult, error) {
	return s.execute(params, limit, useHydeHistory)
}

func TestIndustryModule(t *testing.T) {
	t.Run("必須依存が不足している場合はエラーを返す", func(t *testing.T) {
		module, err := NewModule(Dependencies{})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new semantic usecase factory is required")
	})

	t.Run("正常にモジュール生成できnilレシーバでも安全に扱える", func(t *testing.T) {
		module, err := NewModule(Dependencies{
			NewSemanticUseCase: func(_ logger.LevelLogger) SemanticIndustryUseCase {
				return &stubSemanticSearcher{}
			},
		})
		assert.NoError(t, err)
		assert.NotNil(t, module)
		assert.NotNil(t, module.Handler())

		var nilModule *Module
		assert.Nil(t, nilModule.Handler())
	})

}

func TestIndustrySetup(t *testing.T) {
	e := echo.New()
	err := Setup(e, nil)
	assert.EqualError(t, err, "industry module handler is nil")

	module, _ := NewModule(Dependencies{
		NewSemanticUseCase: func(_ logger.LevelLogger) SemanticIndustryUseCase {
			return &stubSemanticSearcher{}
		},
	})
	assert.NoError(t, Setup(e, module))

	found := false
	for _, r := range e.Routes() {
		if r.Method == http.MethodPost && r.Path == "/industry/search/semantic" {
			found = true
		}
	}
	assert.True(t, found)
}

func TestIndustryHandlerAndMock(t *testing.T) {
	t.Run("バインド済みパラメータの型が不正な場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/industry/search/semantic", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, "invalid")

		h := NewHandler(func(_ logger.LevelLogger) SemanticIndustryUseCase {
			return &stubSemanticSearcher{}
		})
		assert.Equal(t, merr.ErrBadParameter, h.searchSemanticIndustry(c))
	})

	t.Run("検索ユースケースがエラーを返す場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/industry/search/semantic", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.SearchSemanticIndustryRequest{Sentence: "s"})
		h := NewHandler(func(_ logger.LevelLogger) SemanticIndustryUseCase {
			return &stubSemanticSearcher{
				execute: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*dindustry.IndustrySearchResult, error) {
					return nil, errors.New("failed")
				},
			}
		})
		assert.NoError(t, h.searchSemanticIndustry(c))
		assert.Equal(t, http.StatusInternalServerError, rec.Code)
	})

}
