package industry

import (
	dto "aica/api/api/mcptool/http/industry/dto"
	dindustry "aica/api/domain/industry"
	"aica/api/domain/provider"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	mHttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
	"net/http"

	"github.com/labstack/echo/v4"
	"github.com/samber/lo"
)

type SemanticIndustryUseCase interface {
	Execute(params *mHttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*dindustry.IndustrySearchResult, error)
}

type NewSemanticIndustryUseCaseFunc func(l logger.LevelLogger) SemanticIndustryUseCase

type Handler struct {
	newSemanticUseCase NewSemanticIndustryUseCaseFunc
}

func NewHandler(newSemanticUseCase NewSemanticIndustryUseCaseFunc) *Handler {
	return &Handler{
		newSemanticUseCase: newSemanticUseCase,
	}
}

/*
センテンスから業種を検索する

curlリクエスト例：
curl -v -X POST -H "Content-Type: application/json" -d '{"sentence":"スポーツ系の企業"}' http://localhost:10001/aica/mcptool/industry/search/semantic
*/
func (h *Handler) searchSemanticIndustry(c echo.Context) error {
	req, ok := mectx.BoundParam(c).(*dto.SearchSemanticIndustryRequest)
	if !ok || req == nil {
		return merr.ErrBadParameter
	}
	if len(req.Sentence) == 0 {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "sentence is required"})
	}

	if req.Provider == nil {
		tmpProvider := string(provider.DefaultProvider)
		req.Provider = &tmpProvider
	}

	if req.Distance == nil {
		tmpDistance := mHttp.DEFAULT_DISTANCE
		req.Distance = &tmpDistance
	}

	params := mHttp.VectorSearchParams{
		Provider: *req.Provider,
		Keyword:  req.Sentence,
		Distance: float64(*req.Distance),
	}

	limit := lo.FromPtrOr(req.Limit, mHttp.INDUSTRY_JOBTYPE_SEARCH_DEFAULT_LIMIT)

	industries, err := h.newSemanticUseCase(mectx.Logger(c)).Execute(&params, limit, false)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}

	return c.JSON(http.StatusOK, industries)

}
