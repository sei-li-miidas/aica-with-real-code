package validation

import (
	pmodel "aica/api/api/mcptool/usecase/position/model"
	"errors"
	"strings"
)

type PrefectureCityFinder interface {
	ExistsPrefectureCity(prefectureName string, cityName string) bool
}

type PositionValidator struct {
	cacheService PrefectureCityFinder
}

func NewPositionValidator(cacheService PrefectureCityFinder) *PositionValidator {
	return &PositionValidator{
		cacheService: cacheService,
	}
}

// ValidatePositionSearchParams validates parameters for generic position search.
func (pv *PositionValidator) ValidatePositionSearchParams(params *pmodel.GenericPositionSearchParams) error {
	if params == nil {
		return errors.New("request is required")
	}

	if params.GetSalary() <= 0 {
		return errors.New("希望年収は必須なので、ユーザーに聞いて下さい。")
	}
	if !HasNonEmptyJobTypeNames(params.JobtypeNames) {
		return errors.New("職種（JobTypeNames）は必須です。職種名を指定してください。")
	}
	return ValidateLocationRequests(params.Locations, pv.existsPrefectureCity, LocationValidationOptions{})
}

func (pv *PositionValidator) existsPrefectureCity(prefectureName, cityName string) bool {
	return pv.cacheService.ExistsPrefectureCity(prefectureName, cityName)
}

func HasNonEmptyJobTypeNames(names []string) bool {
	for _, name := range names {
		if strings.TrimSpace(name) != "" {
			return true
		}
	}
	return false
}
