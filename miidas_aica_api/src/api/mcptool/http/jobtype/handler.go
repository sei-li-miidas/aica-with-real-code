package jobtype

import (
	dto "aica/api/api/mcptool/http/jobtype/dto"
	jobtypeUC "aica/api/api/mcptool/usecase/jobtype"
	djobtype "aica/api/domain/jobtype"
	"aica/api/domain/provider"
	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	mHttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
	"net/http"

	"github.com/labstack/echo/v4"
	"github.com/samber/lo"
)

type (
	SemanticJobTypeUseCase interface {
		Execute(params *mHttp.VectorSearchParams, limit uint, useHydeHistory bool) ([]*djobtype.JobTypeSearchResult, error)
	}

	NatureJobTypeUseCase interface {
		Execute(natures *jobtypeUC.SearchJobTypesByNatureRequest) ([]*djobtype.JobTypeSearchResult, error)
	}

	NameJobTypeUseCase interface {
		Execute(names []string) ([]*djobtype.JobTypeSmall, error)
	}

	NewSemanticJobTypeUseCaseFunc func(l logger.LevelLogger) SemanticJobTypeUseCase
	NewNatureJobTypeUseCaseFunc   func(l logger.LevelLogger) NatureJobTypeUseCase
	NewNameJobTypeUseCaseFunc     func(l logger.LevelLogger) NameJobTypeUseCase
)

type Handler struct {
	newSemanticUseCase NewSemanticJobTypeUseCaseFunc
	newNatureUseCase   NewNatureJobTypeUseCaseFunc
	newNameUseCase     NewNameJobTypeUseCaseFunc
}

func NewHandler(
	newSemanticUseCase NewSemanticJobTypeUseCaseFunc,
	newNatureUseCase NewNatureJobTypeUseCaseFunc,
	newNameUseCase NewNameJobTypeUseCaseFunc,
) *Handler {
	return &Handler{
		newSemanticUseCase: newSemanticUseCase,
		newNatureUseCase:   newNatureUseCase,
		newNameUseCase:     newNameUseCase,
	}
}

/*
職種の意味情報検索
リクエストパラメーターは SearchSemanticJobTypeRequest

curlリクエスト例：
curl -v -X POST -H "Content-Type: application/json" -d '{"Keyword":"ものを売る仕事"}' http://localhost:10001/aica/mcptool/jobtype/search/semantic
*/
func (h *Handler) searchSemanticJobType(c echo.Context) error {
	req, ok := mectx.BoundParam(c).(*dto.SearchSemanticJobTypeRequest)
	if !ok || req == nil {
		return merr.ErrBadParameter
	}
	if len(req.Keyword) == 0 {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "Keyword is required"})
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
		Keyword:  req.Keyword,
		Distance: float64(*req.Distance),
	}

	limit := lo.FromPtrOr(req.Limit, mHttp.INDUSTRY_JOBTYPE_SEARCH_DEFAULT_LIMIT)

	jobTypes, err := h.newSemanticUseCase(mectx.Logger(c)).Execute(&params, uint(limit), false)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}

	return c.JSON(http.StatusOK, &dto.SearchSemanticJobTypeResponse{
		Keyword:  req.Keyword,
		Jobtypes: jobTypes,
	})
}

/*
性質から職種を検索する
リクエストパラメーターは SearchJobTypeByNatureRequest

curlリクエスト例：
curl -v -X POST -H "Content-Type: application/json" -d '{"JobNaturePreferences":[{"JobNature":"時間的切迫","Preference":"避けたい"},{"JobNature":"屋外作業","Preference":"避けたい"}]}' http://localhost:10001/aica/mcptool/jobtype/search/nature
*/
func (h *Handler) searchJobTypeByNature(c echo.Context) error {
	req, ok := mectx.BoundParam(c).(*dto.SearchJobTypeByNatureRequest)
	if !ok || req == nil {
		return merr.ErrBadParameter
	}
	if len(req.JobNaturePreferences) == 0 {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "JobNaturePreferences is required"})
	}

	if req.MinNatureScore == nil {
		tmpMinNatureScore := DEFAULT_MIN_NATURE_SCORE
		req.MinNatureScore = &tmpMinNatureScore
	}

	if req.MinJobTypeScore == nil {
		tmpMinJobTypeScore := DEFAULT_MIN_JOB_TYPE_SCORE
		req.MinJobTypeScore = &tmpMinJobTypeScore
	}

	if req.MaxPriorExperienceRequired == nil {
		tmpMaxPriorExperienceRequired := DEFAULT_MAX_PRIOR_EXPERIENCE_REQUIRED
		req.MaxPriorExperienceRequired = &tmpMaxPriorExperienceRequired
	}

	useCaseReq := &jobtypeUC.SearchJobTypesByNatureRequest{
		JobNaturePreferences: lo.Map(req.JobNaturePreferences, func(p *dto.JobNaturePreference, _ int) *jobtypeUC.JobNaturePreference {
			return &jobtypeUC.JobNaturePreference{
				JobNature:  p.JobNature,
				Preference: p.Preference,
			}
		}),
		MinNatureScore:             req.MinNatureScore,
		MinJobTypeScore:            req.MinJobTypeScore,
		MaxPriorExperienceRequired: req.MaxPriorExperienceRequired,
	}

	jobTypes, err := h.newNatureUseCase(mectx.Logger(c)).Execute(useCaseReq)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}

	return c.JSON(http.StatusOK, jobTypes)
}

/*
職種名から職種を検索する
リクエストパラメーターは SearchJobTypesByNameRequest

curlリクエスト例：
curl -v -X POST -H "Content-Type: application/json" -d '{"Names":["法人営業"]}' http://localhost:10001/aica/mcptool/jobtype/search/names
*/
func (h *Handler) searchJobTypeByNames(c echo.Context) error {
	req, ok := mectx.BoundParam(c).(*dto.SearchJobTypesByNameRequest)
	if !ok || req == nil {
		return merr.ErrBadParameter
	}
	names := req.Names
	if len(names) == 0 {
		return c.JSON(http.StatusBadRequest, map[string]string{"error": "names is required"})
	}

	jobTypes, err := h.newNameUseCase(mectx.Logger(c)).Execute(names)
	if err != nil {
		return c.JSON(http.StatusInternalServerError, map[string]string{"error": err.Error()})
	}

	results := lo.Map(jobTypes, func(j *djobtype.JobTypeSmall, _ int) *djobtype.JobTypeSearchResult {
		return &djobtype.JobTypeSearchResult{
			ID:          j.ID,
			Name:        j.Name,
			Description: j.Description,
			Distance:    0,
		}
	})

	return c.JSON(http.StatusOK, results)
}
