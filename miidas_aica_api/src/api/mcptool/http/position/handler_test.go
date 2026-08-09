package position

import (
	positionDTO "aica/api/api/mcptool/http/position/dto"
	tmock "aica/api/api/mcptool/testutil/mock"
	positionUC "aica/api/api/mcptool/usecase/position"
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	address "aica/api/api/mcptool/usecase/shared"
	jobfilter "aica/api/domain/jobfilter"
	mectx "aica/api/sdk/echo/context"
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

type stubGenericPersister struct{}

func (s *stubGenericPersister) PersistFromGenericSearchParams(_ string, _ *pmodel.GenericPositionSearchParams) (*jobfilter.JobSearchFilter, error) {
	return nil, nil
}

func newTestEchoContext(body string) echo.Context {
	e := echo.New()
	req := httptest.NewRequest(echo.POST, "/", strings.NewReader(body))
	req.Header.Set(echo.HeaderContentType, echo.MIMEApplicationJSON)
	rec := httptest.NewRecorder()
	c := e.NewContext(req, rec)
	mectx.SetLogger(c, &tmock.MockLogger{})
	return c
}

func TestHandler_ThemeAndSelectionErrorBranches(t *testing.T) {
	t.Run("バインド済みパラメータの型が不正な場合はBadParameterを返す", func(t *testing.T) {
		t.Run("summaries", func(t *testing.T) {
			h := NewHandler(HandlerDependencies{})
			c := newTestEchoContext("")
			mectx.SetBoundParam(c, "invalid")
			assert.Equal(t, merr.ErrBadParameter, h.summaries(c))
		})

		t.Run("searchITEngineer", func(t *testing.T) {
			h := NewHandler(HandlerDependencies{})
			c := newTestEchoContext("")
			mectx.SetBoundParam(c, "invalid")
			assert.Equal(t, merr.ErrBadParameter, h.searchITEngineer(c))
		})

		t.Run("searchFinancialSales", func(t *testing.T) {
			h := NewHandler(HandlerDependencies{})
			c := newTestEchoContext("")
			mectx.SetBoundParam(c, "invalid")
			assert.Equal(t, merr.ErrBadParameter, h.searchFinancialSales(c))
		})

		t.Run("jobTypesSelected", func(t *testing.T) {
			h := NewHandler(HandlerDependencies{})
			c := newTestEchoContext("")
			mectx.SetBoundParam(c, "invalid")
			assert.Equal(t, merr.ErrBadParameter, h.jobTypesSelected(c))
		})

		t.Run("jobTypeSearchFilter", func(t *testing.T) {
			h := NewHandler(HandlerDependencies{})
			c := newTestEchoContext("")
			mectx.SetBoundParam(c, "invalid")
			assert.Equal(t, merr.ErrBadParameter, h.jobTypeSearchFilter(c))
		})
	})

	t.Run("ITエンジニアテーマ検索ユースケース生成でエラーになる場合", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				return nil, errors.New("new uc failed")
			},
		})
		c := newTestEchoContext("")
		err := h.searchITEngineerTheme(c)
		assert.Error(t, err)
	})

	t.Run("金融営業テーマ検索ユースケース生成でエラーになる場合", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				return nil, errors.New("new uc failed")
			},
		})
		c := newTestEchoContext("")
		err := h.searchFinancialSalesTheme(c)
		assert.Error(t, err)
	})

	t.Run("選択職種取得ユースケースが未設定の場合", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{
			NewJobTypesSelectedUseCase: func(logger.LevelLogger) JobTypesSelectedUseCase {
				return nil
			},
		})
		c := newTestEchoContext("")
		mectx.SetBoundParam(c, &positionDTO.JobTypesSelectionRequest{})
		err := h.jobTypesSelected(c)
		assert.Error(t, err)
	})

	t.Run("職種検索フィルタ取得ユースケースが未設定の場合", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{
			NewJobTypeSearchFilterUseCase: func(logger.LevelLogger) JobTypeSearchFilterUseCase {
				return nil
			},
		})
		c := newTestEchoContext("")
		mectx.SetBoundParam(c, &positionDTO.JobTypeSearchFilterRequest{JobtypeName: "ITコンサルタント（アプリ）"})
		err := h.jobTypeSearchFilter(c)
		assert.Error(t, err)
	})

	t.Run("職種名が空の場合は不正なパラメータを返す", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{})
		c := newTestEchoContext("")
		mectx.SetBoundParam(c, &positionDTO.JobTypeSearchFilterRequest{JobtypeName: ""})
		err := h.jobTypeSearchFilter(c)
		assert.Error(t, err)
	})

	t.Run("現在職種検索フィルタ取得ユースケースが未設定の場合", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{
			NewJobTypeSearchFilterUseCase: func(logger.LevelLogger) JobTypeSearchFilterUseCase {
				return nil
			},
		})
		c := newTestEchoContext("")
		err := h.currentJobTypeSearchFilter(c)
		assert.Error(t, err)
	})
}

func TestHandler_SearchJobTypeSpecificInvalidInputBranches(t *testing.T) {
	h := NewHandler(HandlerDependencies{})

	c := newTestEchoContext(`{"JobtypeNames":[]}`)
	assert.Error(t, h.searchJobTypeSpecific(c))

	c = newTestEchoContext(`{"JobtypeNames":[""]}`)
	assert.Error(t, h.searchJobTypeSpecific(c))
}

func TestGenericSearchLocationsFromFilter_PreservesCommutingAreasWithResidence(t *testing.T) {
	locations := &jobfilter.JobSearchFilterLocations{
		Residence: &jobfilter.JobSearchFilterResidence{
			Address: &jobfilter.JobSearchFilterAddress{PrefectureName: "東京都", CityName: "新宿区"},
			CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{
				{Label: "東京都新宿区", PrefectureName: "東京都", CityName: "新宿区", Selected: true},
				{Label: "東京都渋谷区", PrefectureName: "東京都", CityName: "渋谷区", Selected: true},
			},
		},
		WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{
			{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
		},
	}

	got := genericSearchLocationsFromFilter(locations)
	if assert.Len(t, got, 4) {
		assert.Equal(t, address.LOCATION_TYPE_RESIDENCE, got[0].LocationType)

		commutingCities := make([]string, 0, 2)
		for _, item := range got {
			if item.LocationType != address.LOCATION_TYPE_COMMUTING_AREAS {
				continue
			}
			commutingCities = append(commutingCities, item.CityName)
		}
		assert.ElementsMatch(t, []string{"新宿区", "渋谷区"}, commutingCities)
		assert.Equal(t, address.LOCATION_TYPE_WORK_LOCATION, got[3].LocationType)
	}
}

func TestGenericSearchLocationsFromFilter_IgnoresCommutingAreasWithoutResidenceAddress(t *testing.T) {
	locations := &jobfilter.JobSearchFilterLocations{
		Residence: &jobfilter.JobSearchFilterResidence{
			CommutingAreas: []*jobfilter.JobSearchFilterLocationSelectableItem{
				{Label: "東京都渋谷区", PrefectureName: "東京都", CityName: "渋谷区", Selected: true},
			},
		},
		WorkLocations: []*jobfilter.JobSearchFilterLocationSelectableItem{
			{Label: "東京都港区", PrefectureName: "東京都", CityName: "港区", Selected: true},
		},
	}

	got := genericSearchLocationsFromFilter(locations)
	if assert.Len(t, got, 1) {
		assert.Equal(t, address.LOCATION_TYPE_WORK_LOCATION, got[0].LocationType)
		assert.Equal(t, "港区", got[0].CityName)
	}
}

func TestHandler_SearchDispatchByToolName(t *testing.T) {

	t.Run("職種がすべてIT向けなら職種別経路を使う", func(t *testing.T) {
		searchWithJobTypeCalled := false
		genericCalled := false
		h := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				genericCalled = true
				return positionUC.NewGenericSearchUseCase(l, nil, nil, nil, nil, nil, nil)
			},
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				searchWithJobTypeCalled = true
				return nil, errors.New("jobtype path called")
			},
			JobTypeSearchToolResolver: &stubJobTypeSearchToolResolver{
				toolNameByJobtype: map[string]string{
					"ITコンサルタント（アプリ）": pcontracts.ToolNameSearchJobPostingsForITEngineer,
					"Webアプリ開発":       pcontracts.ToolNameSearchJobPostingsForITEngineer,
				},
			},
		})

		c := newTestEchoContext(`{
			"Salary":600,
			"JobtypeNames":["ITコンサルタント（アプリ）","Webアプリ開発"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}]
		}`)
		err := h.searchJobTypeSpecific(c)
		assert.ErrorContains(t, err, "jobtype path called")
		assert.True(t, searchWithJobTypeCalled)
		assert.False(t, genericCalled)
	})

	t.Run("職種が混在するなら汎用経路を使う", func(t *testing.T) {
		searchWithJobTypeCalled := false
		genericCalled := false
		h := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				genericCalled = true
				return positionUC.NewGenericSearchUseCase(
					l,
					&stubMVGateway{},
					nil,
					nil,
					&stubPositionRepo{},
					&stubPositionValidator{},
					&stubLocationLookup{},
				)
			},
			NewJobTypeSmallIDResolver: func(logger.LevelLogger) pcontracts.JobSpecificSearchResolver {
				return &stubJobSpecificResolver{}
			},
			NewGenericSearchFilterPersister: func(logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister {
				return &stubGenericPersister{}
			},
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				searchWithJobTypeCalled = true
				return nil, errors.New("unexpected jobtype path call")
			},
			JobTypeSearchToolResolver: &stubJobTypeSearchToolResolver{
				toolNameByJobtype: map[string]string{
					"ITコンサルタント（アプリ）": pcontracts.ToolNameSearchJobPostingsForITEngineer,
					"金融営業（法人）":       pcontracts.ToolNameSearchJobPostingsForSalesFinancialSales,
				},
			},
		})

		c := newTestEchoContext(`{
			"Salary":600,
			"JobtypeNames":["ITコンサルタント（アプリ）","金融営業（法人）"],
			"Locations":[{"LocationType":"フルリモート"}]
		}`)
		err := h.searchJobTypeSpecific(c)
		assert.NoError(t, err)
		assert.True(t, genericCalled)
		assert.False(t, searchWithJobTypeCalled)
	})

	t.Run("未知の職種を含むなら汎用経路を使う", func(t *testing.T) {
		searchWithJobTypeCalled := false
		genericCalled := false
		h := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				genericCalled = true
				return positionUC.NewGenericSearchUseCase(
					l,
					&stubMVGateway{},
					nil,
					nil,
					&stubPositionRepo{},
					&stubPositionValidator{},
					&stubLocationLookup{},
				)
			},
			NewJobTypeSmallIDResolver: func(logger.LevelLogger) pcontracts.JobSpecificSearchResolver {
				return &stubJobSpecificResolver{}
			},
			NewGenericSearchFilterPersister: func(logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister {
				return &stubGenericPersister{}
			},
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				searchWithJobTypeCalled = true
				return nil, errors.New("unexpected jobtype path call")
			},
			JobTypeSearchToolResolver: &stubJobTypeSearchToolResolver{
				toolNameByJobtype: map[string]string{
					"ITコンサルタント（アプリ）": pcontracts.ToolNameSearchJobPostingsForITEngineer,
				},
			},
		})

		c := newTestEchoContext(`{
			"Salary":600,
			"JobtypeNames":["ITコンサルタント（アプリ）","未知の職種"],
			"Locations":[{"LocationType":"フルリモート"}]
		}`)
		err := h.searchJobTypeSpecific(c)
		assert.NoError(t, err)
		assert.True(t, genericCalled)
		assert.False(t, searchWithJobTypeCalled)
	})
	t.Run("IT向けツール名の場合は職種別経路を使う", func(t *testing.T) {
		searchWithJobTypeCalled := false
		genericCalled := false
		h := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				genericCalled = true
				return positionUC.NewGenericSearchUseCase(l, nil, nil, nil, nil, nil, nil)
			},
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				searchWithJobTypeCalled = true
				return nil, errors.New("jobtype path called")
			},
		})

		c := newTestEchoContext(`{
			"ToolName":"search_job_postings_for_it_engineer",
			"Salary":600,
			"JobtypeNames":["SE"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
			"ProgrammingLanguages":["Go"]
		}`)
		err := h.search(c)
		assert.ErrorContains(t, err, "jobtype path called")
		assert.True(t, searchWithJobTypeCalled)
		assert.False(t, genericCalled)
	})

	t.Run("金融営業向けツール名の場合は職種別経路を使う", func(t *testing.T) {
		searchWithJobTypeCalled := false
		genericCalled := false
		h := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				genericCalled = true
				return positionUC.NewGenericSearchUseCase(l, nil, nil, nil, nil, nil, nil)
			},
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				searchWithJobTypeCalled = true
				return nil, errors.New("jobtype path called")
			},
		})

		c := newTestEchoContext(`{
			"ToolName":"search_job_postings_for_sales_financial_sales",
			"Salary":600,
			"JobtypeNames":["FS"],
			"Locations":[{"LocationType":"居住地","PrefectureName":"東京都","CityName":"新宿区"}],
			"HandledFinancialProducts":["保険"]
		}`)
		err := h.search(c)
		assert.ErrorContains(t, err, "jobtype path called")
		assert.True(t, searchWithJobTypeCalled)
		assert.False(t, genericCalled)
	})

	t.Run("未知のツール名の場合は汎用経路を使う", func(t *testing.T) {
		searchWithJobTypeCalled := false
		genericCalled := false
		h := NewHandler(HandlerDependencies{
			NewGenericSearchUseCase: func(l logger.LevelLogger) GenericSearchUseCase {
				genericCalled = true
				return positionUC.NewGenericSearchUseCase(
					l,
					&stubMVGateway{},
					nil,
					nil,
					&stubPositionRepo{},
					&stubPositionValidator{},
					&stubLocationLookup{},
				)
			},
			NewJobTypeSmallIDResolver: func(logger.LevelLogger) pcontracts.JobSpecificSearchResolver {
				return &stubJobSpecificResolver{}
			},
			NewGenericSearchFilterPersister: func(logger.LevelLogger) pinterfaces.JobSearchFilterGenericPersister {
				return &stubGenericPersister{}
			},
			NewSearchWithJobTypeUseCase: func(_ logger.LevelLogger, _ bool) (SearchWithJobTypeUseCase, error) {
				searchWithJobTypeCalled = true
				return nil, errors.New("unexpected jobtype path call")
			},
		})

		c := newTestEchoContext(`{
			"ToolName":"unknown_tool",
			"Salary":600,
			"JobtypeNames":["SE"],
			"Locations":[{"LocationType":"フルリモート"}]
		}`)
		err := h.search(c)
		assert.NoError(t, err)
		assert.True(t, genericCalled)
		assert.False(t, searchWithJobTypeCalled)
	})

	t.Run("不正なJSONの場合はBadRequestを返す", func(t *testing.T) {
		h := NewHandler(HandlerDependencies{})
		c := newTestEchoContext(`{`)
		err := h.search(c)
		httpErr, ok := err.(*echo.HTTPError)
		assert.True(t, ok)
		assert.Equal(t, http.StatusBadRequest, httpErr.Code)
	})
}
