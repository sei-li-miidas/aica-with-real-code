package jobtype

import (
	"aica/api/domain/jobtype"
	"aica/api/sdk/logger"
)

// SearchJobTypesByNameUseCase
type SearchJobTypesByNameUseCase struct {
	logger logger.LevelLogger
	repo   jobTypeByNameRepository
}

type SearchJobTypesByNameRequest struct {
	Names []string
}

type jobTypeByNameRepository interface {
	GetMultipleByNames(names []string) ([]*jobtype.JobTypeSmall, error)
}

func NewSearchJobTypesByNameUseCaseWithRepository(l logger.LevelLogger, repo jobTypeByNameRepository) *SearchJobTypesByNameUseCase {
	return &SearchJobTypesByNameUseCase{
		logger: l,
		repo:   repo,
	}
}

// Execute 検索
func (uc *SearchJobTypesByNameUseCase) Execute(names []string) ([]*jobtype.JobTypeSmall, error) {
	results, err := uc.repo.GetMultipleByNames(names)
	if err != nil {
		return nil, err
	}

	return results, nil
}
