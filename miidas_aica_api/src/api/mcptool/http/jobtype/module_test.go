package jobtype

import (
	dto "aica/api/api/mcptool/http/jobtype/dto"
	jobtypeUC "aica/api/api/mcptool/usecase/jobtype"
	djobtype "aica/api/domain/jobtype"
	mectx "aica/api/sdk/echo/context"
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
	execute func(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*djobtype.JobTypeSearchResult, error)
}

func (s *stubSemanticSearcher) Execute(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*djobtype.JobTypeSearchResult, error) {
	return s.execute(params, limit, useHydeHistory)
}

type stubNatureSearcher struct {
	execute func(natures *jobtypeUC.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error)
}

func (s *stubNatureSearcher) Execute(natures *jobtypeUC.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error) {
	return s.execute(natures)
}

type stubNameSearcher struct {
	execute func(names []string) ([]*djobtype.JobTypeSmall, error)
}

func (s *stubNameSearcher) Execute(names []string) ([]*djobtype.JobTypeSmall, error) {
	return s.execute(names)
}

func TestJobtypeModule(t *testing.T) {
	t.Run("必須依存が不足している場合はエラーを返す", func(t *testing.T) {
		module, err := NewModule(Dependencies{})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new semantic usecase factory is required")

		module, err = NewModule(Dependencies{
			NewSemanticUseCase: func(_ logger.LevelLogger) SemanticJobTypeUseCase { return &stubSemanticSearcher{} },
		})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new nature usecase factory is required")

		module, err = NewModule(Dependencies{
			NewSemanticUseCase: func(_ logger.LevelLogger) SemanticJobTypeUseCase { return &stubSemanticSearcher{} },
			NewNatureUseCase:   func(_ logger.LevelLogger) NatureJobTypeUseCase { return &stubNatureSearcher{} },
		})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new name usecase factory is required")
	})

	t.Run("正常にモジュール生成できnilレシーバでも安全に扱える", func(t *testing.T) {
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
		assert.NotNil(t, module)
		assert.NotNil(t, module.Handler())

		var nilModule *Module
		assert.Nil(t, nilModule.Handler())
	})

}

func TestJobtypeSetup(t *testing.T) {
	e := echo.New()
	err := Setup(e, nil)
	assert.EqualError(t, err, "jobtype module handler is nil")

	module, _ := NewModule(Dependencies{
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

func TestJobtypeHandlerAndMock(t *testing.T) {
	t.Run("自然言語検索ユースケースがエラーを返す場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/jobtype/search/nature", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.SearchJobTypeByNatureRequest{
			JobNaturePreferences: []*dto.JobNaturePreference{{JobNature: "a", Preference: jobtypeUC.Wanted}},
		})
		h := NewHandler(func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{}
		}, func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{
				execute: func(_ *jobtypeUC.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error) {
					return nil, errors.New("failed")
				},
			}
		}, func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{}
		})
		assert.NoError(t, h.searchJobTypeByNature(c))
		assert.Equal(t, http.StatusInternalServerError, rec.Code)
	})

	t.Run("自然言語検索が成功する場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/jobtype/search/nature", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.SearchJobTypeByNatureRequest{
			JobNaturePreferences: []*dto.JobNaturePreference{{JobNature: "a", Preference: jobtypeUC.Wanted}},
		})
		h := NewHandler(func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{}
		}, func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{
				execute: func(_ *jobtypeUC.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error) {
					return []*djobtype.JobTypeSearchResult{{ID: 1, Name: "営業"}}, nil
				},
			}
		}, func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{}
		})
		assert.NoError(t, h.searchJobTypeByNature(c))
		assert.Equal(t, http.StatusOK, rec.Code)
	})

	t.Run("セマンティック検索ユースケースがエラーを返す場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/jobtype/search/semantic", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.SearchSemanticJobTypeRequest{Keyword: "k"})
		h := NewHandler(func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{
				execute: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*djobtype.JobTypeSearchResult, error) {
					return nil, errors.New("failed")
				},
			}
		}, func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{}
		}, func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameSearcher{}
		})
		assert.NoError(t, h.searchSemanticJobType(c))
		assert.Equal(t, http.StatusInternalServerError, rec.Code)
	})

}
