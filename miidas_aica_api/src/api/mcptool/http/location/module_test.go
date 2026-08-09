package location

import (
	dto "aica/api/api/mcptool/http/location/dto"
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/labstack/echo/v4"
	"github.com/stretchr/testify/assert"
)

type stubLevelLogger struct{}

func (l *stubLevelLogger) Info(string, ...any)  {}
func (l *stubLevelLogger) Warn(string, ...any)  {}
func (l *stubLevelLogger) Error(string, ...any) {}
func (l *stubLevelLogger) Fatal(string, ...any) {}

type stubVerifyPrefectureCityUseCase struct {
	execute func(reqs []*shared.LocationRequest) master.PrefectureCities
}

func (s *stubVerifyPrefectureCityUseCase) Execute(reqs []*shared.LocationRequest) master.PrefectureCities {
	return s.execute(reqs)
}

type stubSearchCommutingAreasUseCase struct {
	execute func(req *shared.LocationRequest) master.PrefectureCities
}

func (s *stubSearchCommutingAreasUseCase) Execute(req *shared.LocationRequest) master.PrefectureCities {
	return s.execute(req)
}

type stubSearchByKeywordUseCase struct {
	execute func(keyword string) master.PrefectureCities
}

func (s *stubSearchByKeywordUseCase) Execute(keyword string) master.PrefectureCities {
	return s.execute(keyword)
}

func testVerifyFactory() NewVerifyPrefectureCityUseCaseFunc {
	return func(_ logger.LevelLogger) VerifyPrefectureCityUseCase {
		return &stubVerifyPrefectureCityUseCase{
			execute: func(_ []*shared.LocationRequest) master.PrefectureCities { return nil },
		}
	}
}

func testSearchCommutingFactory() NewSearchCommutingAreasUseCaseFunc {
	return func(_ logger.LevelLogger) SearchCommutingAreasUseCase {
		return &stubSearchCommutingAreasUseCase{
			execute: func(_ *shared.LocationRequest) master.PrefectureCities { return nil },
		}
	}
}

func testSearchByKeywordFactory() NewSearchByKeywordUseCaseFunc {
	return func(_ logger.LevelLogger) SearchByKeywordUseCase {
		return &stubSearchByKeywordUseCase{
			execute: func(_ string) master.PrefectureCities { return nil },
		}
	}
}

func TestNewModule(t *testing.T) {
	t.Run("都道府県市区町村検証ユースケースファクトリがnilの場合はエラーを返す", func(t *testing.T) {
		module, err := NewModule(Dependencies{})
		assert.Nil(t, module)
		assert.EqualError(t, err, "new verify prefecture city usecase factory is required")
	})

	t.Run("正常に処理できる", func(t *testing.T) {
		module, err := NewModule(Dependencies{
			NewVerifyPrefectureCityUseCase: testVerifyFactory(),
			NewSearchCommutingAreasUseCase: testSearchCommutingFactory(),
			NewSearchByKeywordUseCase:      testSearchByKeywordFactory(),
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
	t.Run("モジュールがnilの場合はエラーを返す", func(t *testing.T) {
		e := echo.New()
		err := Setup(e, nil)
		assert.EqualError(t, err, "location module handler is nil")
	})

	t.Run("ルートを登録できる", func(t *testing.T) {
		e := echo.New()
		module, err := NewModule(Dependencies{
			NewVerifyPrefectureCityUseCase: testVerifyFactory(),
			NewSearchCommutingAreasUseCase: testSearchCommutingFactory(),
			NewSearchByKeywordUseCase:      testSearchByKeywordFactory(),
		})
		assert.NoError(t, err)
		assert.NoError(t, Setup(e, module))

		paths := map[string]bool{
			"/location/verify/prefecture/city": false,
			"/location/search/commuting_areas": false,
			"/location/search/keyword":         false,
		}
		for _, r := range e.Routes() {
			if _, ok := paths[r.Path]; ok && r.Method == http.MethodPost {
				paths[r.Path] = true
			}
		}
		for path, found := range paths {
			assert.True(t, found, path)
		}
	})
}

func TestHandlerVerifyPrefectureCity(t *testing.T) {
	t.Run("バインド済みパラメータの型が不正な場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/verify/prefecture/city", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.SearchByKeywordRequest{Keyword: "新宿"})

		h := NewHandler(testVerifyFactory(), testSearchCommutingFactory(), testSearchByKeywordFactory())
		err := h.verifyPrefectureCity(c)
		assert.Equal(t, merr.ErrBadParameter, err)
	})

	t.Run("市区町村名が不正な場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/verify/prefecture/city", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.VerifyPrefectureCityRequest{
			Locations: []dto.LocationRequest{
				{PrefectureName: "東京都"},
			},
		})

		h := NewHandler(testVerifyFactory(), testSearchCommutingFactory(), testSearchByKeywordFactory())
		err := h.verifyPrefectureCity(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusBadRequest, rec.Code)
	})

	t.Run("正常に複数件を処理できる", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/verify/prefecture/city", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.VerifyPrefectureCityRequest{
			Locations: []dto.LocationRequest{
				{PrefectureName: "東京都", CityName: "新宿区"},
				{PrefectureName: "東京都", CityName: "渋谷区"},
			},
		})

		h := NewHandler(
			func(_ logger.LevelLogger) VerifyPrefectureCityUseCase {
				return &stubVerifyPrefectureCityUseCase{
					execute: func(_ []*shared.LocationRequest) master.PrefectureCities {
						return master.PrefectureCities{
							{PrefectureID: 13, PrefectureName: "東京都", CityID: 13104, CityName: "新宿区"},
							{PrefectureID: 13, PrefectureName: "東京都", CityID: 13113, CityName: "渋谷区"},
						}
					},
				}
			},
			testSearchCommutingFactory(),
			testSearchByKeywordFactory(),
		)
		err := h.verifyPrefectureCity(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusOK, rec.Code)
		assert.True(t, strings.Contains(rec.Body.String(), "新宿区"))
		assert.True(t, strings.Contains(rec.Body.String(), "渋谷区"))
	})
}

func TestHandlerSearchCommutingAreas(t *testing.T) {
	t.Run("バインド済みパラメータの型が不正な場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/search/commuting_areas", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.SearchByKeywordRequest{Keyword: "新宿"})

		h := NewHandler(testVerifyFactory(), testSearchCommutingFactory(), testSearchByKeywordFactory())
		err := h.searchCommutingAreas(c)
		assert.Equal(t, merr.ErrBadParameter, err)
	})

	t.Run("市区町村名が不正な場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/search/commuting_areas", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.LocationRequest{PrefectureName: "東京都"})

		h := NewHandler(testVerifyFactory(), testSearchCommutingFactory(), testSearchByKeywordFactory())
		err := h.searchCommutingAreas(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusBadRequest, rec.Code)
	})

	t.Run("正常に処理できる", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/search/commuting_areas", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.LocationRequest{PrefectureName: "東京都", CityName: "新宿区"})

		h := NewHandler(
			testVerifyFactory(),
			func(_ logger.LevelLogger) SearchCommutingAreasUseCase {
				return &stubSearchCommutingAreasUseCase{
					execute: func(_ *shared.LocationRequest) master.PrefectureCities {
						return master.PrefectureCities{
							{PrefectureName: "東京都", CityName: "渋谷区"},
						}
					},
				}
			},
			testSearchByKeywordFactory(),
		)
		err := h.searchCommutingAreas(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusOK, rec.Code)
		assert.True(t, strings.Contains(rec.Body.String(), "渋谷区"))
	})
}

func TestHandlerSearchByKeyword(t *testing.T) {
	t.Run("バインド済みパラメータの型が不正な場合", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/search/keyword", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetBoundParam(c, &dto.LocationRequest{PrefectureName: "東京都", CityName: "新宿区"})

		h := NewHandler(testVerifyFactory(), testSearchCommutingFactory(), testSearchByKeywordFactory())
		err := h.searchByKeyword(c)
		assert.Equal(t, merr.ErrBadParameter, err)
	})

	t.Run("正常に処理できる", func(t *testing.T) {
		e := echo.New()
		req := httptest.NewRequest(http.MethodPost, "/location/search/keyword", nil)
		rec := httptest.NewRecorder()
		c := e.NewContext(req, rec)
		mectx.SetLogger(c, &stubLevelLogger{})
		mectx.SetBoundParam(c, &dto.SearchByKeywordRequest{Keyword: "新宿"})

		h := NewHandler(
			testVerifyFactory(),
			testSearchCommutingFactory(),
			func(_ logger.LevelLogger) SearchByKeywordUseCase {
				return &stubSearchByKeywordUseCase{
					execute: func(_ string) master.PrefectureCities {
						return master.PrefectureCities{
							{
								PrefectureID:   13,
								PrefectureName: "東京都",
								CityID:         13104,
								CityName:       "新宿区",
								Name:           "東京都新宿区",
							},
						}
					},
				}
			},
		)
		err := h.searchByKeyword(c)
		assert.NoError(t, err)
		assert.Equal(t, http.StatusOK, rec.Code)
		assert.True(t, strings.Contains(rec.Body.String(), "\"CityID\":13104"))
	})
}
