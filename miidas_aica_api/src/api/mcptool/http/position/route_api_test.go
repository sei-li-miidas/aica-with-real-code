package position

import (
	"aica/api/api/mcptool/service"
	tmock "aica/api/api/mcptool/testutil/mock"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	"aica/api/domain/jobfilter"
	mecho "aica/api/sdk/echo"
	mectx "aica/api/sdk/echo/context"
	mlogger "aica/api/sdk/logger"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"slices"
	"strings"
	"testing"

	"github.com/labstack/echo/v4"
	"gorm.io/gorm"
)

type stubJobSearchFilterReader struct {
	getBySessionID func(sessionID string) (*jobfilter.JobSearchFilter, error)
}

type recordingLogger struct {
	errorMessages []string
}

func (l *recordingLogger) Info(string, ...any)  {}
func (l *recordingLogger) Warn(string, ...any)  {}
func (l *recordingLogger) Fatal(string, ...any) {}
func (l *recordingLogger) Error(message string, _ ...any) {
	l.errorMessages = append(l.errorMessages, message)
}

func (s *stubJobSearchFilterReader) GetBySessionID(sessionID string) (*jobfilter.JobSearchFilter, error) {
	return s.getBySessionID(sessionID)
}

func TestSetup_FailsWhenModuleIsNilOrHandlerNil(t *testing.T) {
	e := echo.New()

	if err := Setup(e, nil); err == nil {
		t.Fatalf("expected error when module is nil")
	}

	if err := Setup(e, &Module{}); err == nil {
		t.Fatalf("expected error when module handler is nil")
	}
}

func TestPositionAPIs_BadJSONReturnsBadRequest(t *testing.T) {
	e := echo.New()
	module := &Module{handler: NewHandler(HandlerDependencies{})}
	if err := Setup(e, module); err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	tests := []string{
		"/positions/search",
		"/positions/search/jobtype_specific",
		"/positions/search/it_engineer",
		"/positions/search/financial_sales",
		"/positions/summaries",
	}

	for _, path := range tests {
		req := httptest.NewRequest(http.MethodPost, path, strings.NewReader("{"))
		req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
		rec := httptest.NewRecorder()

		e.ServeHTTP(rec, req)

		if rec.Code != http.StatusBadRequest {
			t.Fatalf("path=%s expected 400 got %d body=%s", path, rec.Code, rec.Body.String())
		}
	}
}

func TestPositionDetail_InvalidPositionIDReturnsError(t *testing.T) {
	e := echo.New()
	module := &Module{handler: NewHandler(HandlerDependencies{})}
	if err := Setup(e, module); err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	req := httptest.NewRequest(http.MethodPost, "/positions/detail/not-int", nil)
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)

	// Invalid path param is rejected in handler before use case execution.
	if rec.Code < http.StatusBadRequest {
		t.Fatalf("expected an error status, got %d", rec.Code)
	}
}

func TestPositionAPIs_WithRealModule_ValidationAndSuccess(t *testing.T) {
	logger := &tmock.MockLogger{}
	providerRepositoryRegistry := service.NewProviderRepositoryRegistry(logger)
	module, err := NewModule(Dependencies{
		Logger:                     logger,
		CacheService:               service.NewMiidasCacheService(logger, makeInitializedMasterCacheProvider(), providerRepositoryRegistry),
		ProviderRepositoryRegistry: providerRepositoryRegistry,
		LocationLookup:             makeInitializedLocationLookupService(logger, makeInitializedMasterCacheProvider()),
		MVGateway:                  &stubMVGateway{},
		AgentDBProvider:            func() *gorm.DB { return &gorm.DB{} },
		MiidasDBProvider:           func() *gorm.DB { return &gorm.DB{} },
	})
	if err != nil {
		t.Fatalf("failed to create module: %v", err)
	}

	e, err := newMockBootstrapServer(logger, module)
	if err != nil {
		t.Fatalf("setup failed: %v", err)
	}

	t.Run("summariesが空でもDBアクセスせず成功する", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/summaries", `{"PositionIDs":[]}`)
		if rec.Code != http.StatusOK {
			t.Fatalf("expected 200 got %d body=%s", rec.Code, rec.Body.String())
		}

		var body map[string]any
		if err := json.Unmarshal(rec.Body.Bytes(), &body); err != nil {
			t.Fatalf("invalid json: %v", err)
		}
		if _, ok := body["Positions"]; !ok {
			t.Fatalf("expected Positions field in response")
		}
	})

	t.Run("汎用検索で不正な年収がユースケース検証に到達する", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search", `{
			"Salary":0,
			"Locations":[{"LocationType":"フルリモート"}]
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("保存済みフィルタがないレコメンド検索はエラーを返す", func(t *testing.T) {
		e2 := echo.New()
		module2 := &Module{handler: NewHandler(HandlerDependencies{
			NewJobSearchFilterReader: func(mlogger.LevelLogger) pinterfaces.JobSearchFilterReader {
				return &stubJobSearchFilterReader{getBySessionID: func(string) (*jobfilter.JobSearchFilter, error) {
					return nil, nil
				}}
			},
			NewGenericSearchUseCase: func(mlogger.LevelLogger) GenericSearchUseCase { return nil },
		})}
		if err := Setup(e2, module2); err != nil {
			t.Fatalf("setup failed: %v", err)
		}
		rec := performJSONRequestWithHeader(e2, http.MethodGet, "/positions/recommendations/theme1", "", "session-missing-filter")
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("レコメンド検索で保存済みフィルタ取得エラーはログされる", func(t *testing.T) {
		logger2 := &recordingLogger{}
		e2, err := newMockBootstrapServer(logger2, &Module{handler: NewHandler(HandlerDependencies{
			NewJobSearchFilterReader: func(mlogger.LevelLogger) pinterfaces.JobSearchFilterReader {
				return &stubJobSearchFilterReader{getBySessionID: func(string) (*jobfilter.JobSearchFilter, error) {
					return nil, errors.New("reader failed")
				}}
			},
		})})
		if err != nil {
			t.Fatalf("setup failed: %v", err)
		}
		rec := performJSONRequestWithHeader(e2, http.MethodGet, "/positions/recommendations/theme1", "", "session-reader-error")
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
		if !slices.Contains(logger2.errorMessages, "failed to get job_search_filter for recommendations") {
			t.Fatalf("expected recommendations read error to be logged, got: %#v", logger2.errorMessages)
		}
	})

	t.Run("IT検索で不正な年収の場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/it_engineer", `{
			"Salary":0,
			"JobtypeNames":["SE"],
			"RemoteWork":"条件なし"
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("ITテーマ検索で不正な年収の場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/it_engineer/theme1", `{
			"Salary":0,
			"JobtypeNames":["SE"],
			"RemoteWork":"条件なし"
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("金融営業検索で不正な年収の場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/financial_sales", `{
			"Salary":0,
			"JobtypeNames":["金融営業"]
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
	})

	t.Run("金融営業テーマ検索で不正な年収の場合", func(t *testing.T) {
		rec := performJSONRequest(e, "/positions/search/financial_sales/theme1", `{
			"Salary":0,
			"JobtypeNames":["金融営業"]
		}`)
		if rec.Code < http.StatusBadRequest {
			t.Fatalf("expected error status got %d body=%s", rec.Code, rec.Body.String())
		}
	})
}

func performJSONRequest(e *echo.Echo, path, body string) *httptest.ResponseRecorder {
	req := httptest.NewRequest(http.MethodPost, path, strings.NewReader(body))
	req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	rec := httptest.NewRecorder()
	e.ServeHTTP(rec, req)
	return rec
}

func newMockBootstrapServer(l mlogger.LevelLogger, module *Module) (*echo.Echo, error) {
	e := mecho.NewDefaultServer(0)
	e.Use(func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			mectx.SetLogger(c, l)
			return next(c)
		}
	})
	mecho.SetupDefaultRoute(e)
	if err := Setup(e, module); err != nil {
		return nil, err
	}
	return e, nil
}
