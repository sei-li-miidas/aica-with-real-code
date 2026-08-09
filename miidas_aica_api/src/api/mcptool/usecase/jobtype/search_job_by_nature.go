package jobtype

import (
	"aica/api/domain/jobtype"
	"aica/api/sdk/logger"
)

// SearchJobTypesByNatureUseCase
type SearchJobTypesByNatureUseCase struct {
	logger logger.LevelLogger
	repo   jobTypeByNatureRepository
}

type jobTypeByNatureRepository interface {
	SearchByNature(wantedNatures []string, unwantedNatures []string, minNatureScore float32, minJobTypeScore float32, maxPriorExperienceRequired float32) ([]*jobtype.JobTypeSearchResult, error)
}

func NewSearchJobTypesByNatureUseCaseWithRepository(l logger.LevelLogger, repo jobTypeByNatureRepository) *SearchJobTypesByNatureUseCase {
	return &SearchJobTypesByNatureUseCase{
		logger: l,
		repo:   repo,
	}
}

type (
	SearchJobTypesByNatureRequest struct {
		JobNaturePreferences       []*JobNaturePreference
		MinNatureScore             *float32
		MinJobTypeScore            *float32
		MaxPriorExperienceRequired *float32
	}

	JobNaturePreference struct {
		JobNature  string
		Preference string
	}
)

const (
	Wanted   = "やりたい"
	Unwanted = "避けたい"
	Whatever = "どっちでもいい"
)

// Execute 検索
func (uc *SearchJobTypesByNatureUseCase) Execute(natures *SearchJobTypesByNatureRequest) ([]*jobtype.JobTypeSearchResult, error) {
	var wantedNatures, unwantedNatures []string

	for _, nature := range natures.JobNaturePreferences {
		switch nature.Preference {
		case Wanted:
			wantedNatures = append(wantedNatures, nature.JobNature)
		case Unwanted:
			unwantedNatures = append(unwantedNatures, nature.JobNature)
		}
	}

	results, err := uc.repo.SearchByNature(wantedNatures, unwantedNatures, *natures.MinNatureScore, *natures.MinJobTypeScore, *natures.MaxPriorExperienceRequired)
	if err != nil {
		return nil, err
	}

	return results, nil
}
