package jobtype

import (
	dto "aica/api/api/mcptool/http/jobtype/dto"
	jobtypeUC "aica/api/api/mcptool/usecase/jobtype"
	djobtype "aica/api/domain/jobtype"
	mhttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
	"bytes"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/labstack/echo/v4"
)

type noopValidator struct{}

func (n *noopValidator) Validate(_ interface{}) error { return nil }

type stubSemanticJobTypeUseCase struct {
	executeFn func(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*djobtype.JobTypeSearchResult, error)
}

func (s *stubSemanticJobTypeUseCase) Execute(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*djobtype.JobTypeSearchResult, error) {
	return s.executeFn(params, limit, useHydeHistory)
}

type stubNameJobTypeUseCase struct {
	executeFn func(names []string) ([]*djobtype.JobTypeSmall, error)
}

func (s *stubNameJobTypeUseCase) Execute(names []string) ([]*djobtype.JobTypeSmall, error) {
	return s.executeFn(names)
}

func performJobTypeJSONRequest(e *echo.Echo, method, path, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, bytes.NewBufferString(body))
	req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)
	return rec
}

func TestSemanticJobTypeAPI_DefaultsAndDelegation(t *testing.T) {
	called := false
	factory := func(_ logger.LevelLogger) SemanticJobTypeUseCase {
		return &stubSemanticJobTypeUseCase{
			executeFn: func(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*djobtype.JobTypeSearchResult, error) {
				called = true
				if params.Provider == "" {
					t.Fatalf("provider should be defaulted")
				}
				if params.Distance != mhttp.DEFAULT_DISTANCE {
					t.Fatalf("unexpected default distance: %v", params.Distance)
				}
				if params.Keyword != "SE" {
					t.Fatalf("unexpected keyword: %s", params.Keyword)
				}
				if limit != uint(mhttp.INDUSTRY_JOBTYPE_SEARCH_DEFAULT_LIMIT) {
					t.Fatalf("unexpected default limit: %d", limit)
				}
				if useHydeHistory {
					t.Fatalf("useHydeHistory should be false")
				}
				return []*djobtype.JobTypeSearchResult{{ID: 123}}, nil
			},
		}
	}

	e := echo.New()
	e.Validator = &noopValidator{}
	module, err := NewModule(Dependencies{
		NewSemanticUseCase: factory,
		NewNatureUseCase: func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{}
		},
		NewNameUseCase: func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameJobTypeUseCase{
				executeFn: func(_ []string) ([]*djobtype.JobTypeSmall, error) {
					return nil, nil
				},
			}
		},
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}
	if err := Setup(e, module); err != nil {
		t.Fatalf("failed to setup routes: %v", err)
	}
	rec := performJobTypeJSONRequest(e, http.MethodPost, "/jobtype/search/semantic", `{"keyword":"SE"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("unexpected status: %d body=%s", rec.Code, rec.Body.String())
	}
	if !called {
		t.Fatalf("expected usecase to be called")
	}

	var got dto.SearchSemanticJobTypeResponse
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatalf("failed to unmarshal response: %v", err)
	}
	if got.Keyword != "SE" {
		t.Fatalf("unexpected keyword: %#v", got)
	}
	if len(got.Jobtypes) != 1 || got.Jobtypes[0].ID != 123 {
		t.Fatalf("unexpected response: %#v", got)
	}
}

func TestSemanticJobTypeAPI_UsecaseError(t *testing.T) {
	factory := func(_ logger.LevelLogger) SemanticJobTypeUseCase {
		return &stubSemanticJobTypeUseCase{
			executeFn: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*djobtype.JobTypeSearchResult, error) {
				return nil, errors.New("failed")
			},
		}
	}

	e := echo.New()
	e.Validator = &noopValidator{}
	module, err := NewModule(Dependencies{
		NewSemanticUseCase: factory,
		NewNatureUseCase: func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{}
		},
		NewNameUseCase: func(_ logger.LevelLogger) NameJobTypeUseCase {
			return &stubNameJobTypeUseCase{
				executeFn: func(_ []string) ([]*djobtype.JobTypeSmall, error) {
					return nil, nil
				},
			}
		},
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}
	if err := Setup(e, module); err != nil {
		t.Fatalf("failed to setup routes: %v", err)
	}
	rec := performJobTypeJSONRequest(e, http.MethodPost, "/jobtype/search/semantic", `{"keyword":"SE"}`)
	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("unexpected status: %d body=%s", rec.Code, rec.Body.String())
	}
}

var _ SemanticJobTypeUseCase = (*jobtypeUC.SearchUseCase)(nil)

func TestSearchJobTypeByNamesAPI_SuccessDistanceZero(t *testing.T) {
	factory := func(_ logger.LevelLogger) NameJobTypeUseCase {
		return &stubNameJobTypeUseCase{
			executeFn: func(names []string) ([]*djobtype.JobTypeSmall, error) {
				if len(names) != 1 || names[0] != "法人営業" {
					t.Fatalf("unexpected names: %#v", names)
				}
				return []*djobtype.JobTypeSmall{{ID: 1, Name: "法人営業", Description: "desc"}}, nil
			},
		}
	}

	e := echo.New()
	e.Validator = &noopValidator{}
	module, err := NewModule(Dependencies{
		NewSemanticUseCase: func(_ logger.LevelLogger) SemanticJobTypeUseCase {
			return &stubSemanticSearcher{}
		},
		NewNatureUseCase: func(_ logger.LevelLogger) NatureJobTypeUseCase {
			return &stubNatureSearcher{}
		},
		NewNameUseCase: factory,
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}
	if err := Setup(e, module); err != nil {
		t.Fatalf("failed to setup routes: %v", err)
	}

	rec := performJobTypeJSONRequest(e, http.MethodPost, "/jobtype/search/names", `{"names":["法人営業"]}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("unexpected status: %d body=%s", rec.Code, rec.Body.String())
	}

	var got []*djobtype.JobTypeSearchResult
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatalf("failed to unmarshal response: %v", err)
	}
	if len(got) != 1 {
		t.Fatalf("unexpected response length: %#v", got)
	}
	if got[0].Name != "法人営業" || got[0].Distance != 0 {
		t.Fatalf("unexpected response payload: %#v", got[0])
	}
}
