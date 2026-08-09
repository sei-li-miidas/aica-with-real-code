package location

import (
	dto "aica/api/api/mcptool/http/location/dto"
	"aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"net/http"

	"github.com/labstack/echo/v4"
	"github.com/samber/lo"
)

type (
	VerifyPrefectureCityUseCase interface {
		Execute(reqs []*shared.LocationRequest) master.PrefectureCities
	}

	SearchCommutingAreasUseCase interface {
		Execute(req *shared.LocationRequest) master.PrefectureCities
	}

	SearchByKeywordUseCase interface {
		Execute(keyword string) master.PrefectureCities
	}

	NewVerifyPrefectureCityUseCaseFunc func(l logger.LevelLogger) VerifyPrefectureCityUseCase
	NewSearchCommutingAreasUseCaseFunc func(l logger.LevelLogger) SearchCommutingAreasUseCase
	NewSearchByKeywordUseCaseFunc      func(l logger.LevelLogger) SearchByKeywordUseCase
)

type Handler struct {
	newVerifyPrefectureCityUseCase NewVerifyPrefectureCityUseCaseFunc
	newSearchCommutingAreasUseCase NewSearchCommutingAreasUseCaseFunc
	newSearchByKeywordUseCase      NewSearchByKeywordUseCaseFunc
}

func toSharedLocationRequest(req *dto.LocationRequest) *shared.LocationRequest {
	return &shared.LocationRequest{
		LocationType:   shared.LOCATION_TYPE_RESIDENCE,
		PrefectureName: req.PrefectureName,
		CityName:       req.CityName,
	}
}

func toSharedLocationRequests(reqs []dto.LocationRequest) []*shared.LocationRequest {
	return lo.Map(reqs, func(req dto.LocationRequest, _ int) *shared.LocationRequest {
		return toSharedLocationRequest(&req)
	})
}

func NewHandler(
	newVerifyPrefectureCityUseCase NewVerifyPrefectureCityUseCaseFunc,
	newSearchCommutingAreasUseCase NewSearchCommutingAreasUseCaseFunc,
	newSearchByKeywordUseCase NewSearchByKeywordUseCaseFunc,
) *Handler {
	return &Handler{
		newVerifyPrefectureCityUseCase: newVerifyPrefectureCityUseCase,
		newSearchCommutingAreasUseCase: newSearchCommutingAreasUseCase,
		newSearchByKeywordUseCase:      newSearchByKeywordUseCase,
	}
}

func verifyPrefectureCityRequests(c echo.Context) ([]dto.LocationRequest, error) {
	req, ok := mectx.BoundParam(c).(*dto.VerifyPrefectureCityRequest)
	if !ok || req == nil || len(req.Locations) == 0 {
		return nil, merr.ErrBadParameter
	}

	return req.Locations, nil
}

func (h *Handler) verifyPrefectureCity(c echo.Context) error {
	reqs, err := verifyPrefectureCityRequests(c)
	if err != nil {
		return merr.ErrBadParameter
	}

	for _, req := range reqs {
		if req.CityName == "" {
			return c.JSON(http.StatusBadRequest, map[string]string{"error": "Invalid city name"})
		}
	}

	cities := h.newVerifyPrefectureCityUseCase(mectx.Logger(c)).Execute(toSharedLocationRequests(reqs))

	return c.JSON(http.StatusOK, cities)
}

func (h *Handler) searchCommutingAreas(c echo.Context) error {
	req, ok := mectx.BoundParam(c).(*dto.LocationRequest)
	if !ok || req == nil {
		return merr.ErrBadParameter
	}
	// 居住地からの通勤圏検索にLocationType無視
	if req.CityName == "" {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "Invalid city name"})
	}

	commutingAreas := h.newSearchCommutingAreasUseCase(mectx.Logger(c)).Execute(toSharedLocationRequest(req))

	return c.JSON(http.StatusOK, commutingAreas)
}

// マスターキャッシュを使って都道府県、市区町村の検索を行います。
// keyword: 検索キーワード
// マッチングされた都道府県、市区町村一覧を返します。
func (h *Handler) searchByKeyword(c echo.Context) error {
	req, ok := mectx.BoundParam(c).(*dto.SearchByKeywordRequest)
	if !ok || req == nil {
		return merr.ErrBadParameter
	}
	cities := h.newSearchByKeywordUseCase(mectx.Logger(c)).Execute(req.Keyword)

	return c.JSON(http.StatusOK, lo.Map(cities, func(city *master.PrefectureCity, _ int) map[string]any {
		return map[string]any{
			"PrefectureID":   city.PrefectureID,
			"PrefectureName": city.PrefectureName,
			"CityID":         city.CityID,
			"CityName":       city.CityName,
			"Name":           city.Name,
		}
	}))
}
