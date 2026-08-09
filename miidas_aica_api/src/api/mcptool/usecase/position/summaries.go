package position

import (
	pinterfaces "aica/api/api/mcptool/usecase/position/interfaces"
	pmodel "aica/api/api/mcptool/usecase/position/model"
	psupport "aica/api/api/mcptool/usecase/position/support"
	"aica/api/domain/user/apply/position"
	"aica/api/sdk/logger"
)

type (
	SummariesUseCase struct {
		logger             logger.LevelLogger
		positionRepository pinterfaces.PositionGetter
	}
)

func NewSummariesUseCase(l logger.LevelLogger, positionRepository pinterfaces.PositionGetter) *SummariesUseCase {
	return &SummariesUseCase{
		logger:             l,
		positionRepository: positionRepository,
	}
}

func (uc *SummariesUseCase) Execute(positionIds []position.ID) ([]*pmodel.PositionSummary, error) {
	return psupport.FillPositionData(uc.positionRepository, uc.logger, positionIds)
}
