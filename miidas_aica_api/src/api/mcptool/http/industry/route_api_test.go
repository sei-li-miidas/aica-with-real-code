package industry

import (
	dindustry "aica/api/domain/industry"
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

type stubSemanticIndustryUseCase struct {
	executeFn func(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*dindustry.IndustrySearchResult, error)
}

func (s *stubSemanticIndustryUseCase) Execute(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*dindustry.IndustrySearchResult, error) {
	return s.executeFn(params, limit, useHydeHistory)
}

func performIndustryJSONRequest(e *echo.Echo, method, path, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(method, path, bytes.NewBufferString(body))
	req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)
	return rec
}

func TestSemanticIndustryAPI_DefaultsAndDelegation(t *testing.T) {
	called := false
	factory := func(_ logger.LevelLogger) SemanticIndustryUseCase {
		return &stubSemanticIndustryUseCase{
			executeFn: func(params *mhttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*dindustry.IndustrySearchResult, error) {
				called = true
				if params.Provider == "" {
					t.Fatalf("provider should be defaulted")
				}
				if params.Distance != mhttp.DEFAULT_DISTANCE {
					t.Fatalf("unexpected default distance: %v", params.Distance)
				}
				if params.Keyword != "SaaS" {
					t.Fatalf("unexpected keyword: %s", params.Keyword)
				}
				if limit != mhttp.INDUSTRY_JOBTYPE_SEARCH_DEFAULT_LIMIT {
					t.Fatalf("unexpected default limit: %d", limit)
				}
				if useHydeHistory {
					t.Fatalf("useHydeHistory should be false")
				}
				return []*dindustry.IndustrySearchResult{{ID: 77}}, nil
			},
		}
	}

	e := echo.New()
	e.Validator = &noopValidator{}
	module, err := NewModule(Dependencies{
		NewSemanticUseCase: factory,
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}
	if err := Setup(e, module); err != nil {
		t.Fatalf("failed to setup routes: %v", err)
	}
	rec := performIndustryJSONRequest(e, http.MethodPost, "/industry/search/semantic", `{"sentence":"SaaS"}`)
	if rec.Code != http.StatusOK {
		t.Fatalf("unexpected status: %d body=%s", rec.Code, rec.Body.String())
	}
	if !called {
		t.Fatalf("expected usecase to be called")
	}

	var got []*dindustry.IndustrySearchResult
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatalf("failed to unmarshal response: %v", err)
	}
	if len(got) != 1 || got[0].ID != 77 {
		t.Fatalf("unexpected response: %#v", got)
	}
}

func TestSemanticIndustryAPI_UsecaseError(t *testing.T) {
	factory := func(_ logger.LevelLogger) SemanticIndustryUseCase {
		return &stubSemanticIndustryUseCase{
			executeFn: func(_ *mhttp.VectorSearchParams, _ uint, _ bool) ([]*dindustry.IndustrySearchResult, error) {
				return nil, errors.New("failed")
			},
		}
	}

	e := echo.New()
	e.Validator = &noopValidator{}
	module, err := NewModule(Dependencies{
		NewSemanticUseCase: factory,
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}
	if err := Setup(e, module); err != nil {
		t.Fatalf("failed to setup routes: %v", err)
	}
	rec := performIndustryJSONRequest(e, http.MethodPost, "/industry/search/semantic", `{"sentence":"SaaS"}`)
	if rec.Code != http.StatusInternalServerError {
		t.Fatalf("unexpected status: %d body=%s", rec.Code, rec.Body.String())
	}
}
