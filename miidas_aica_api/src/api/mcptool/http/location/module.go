package location

import (
	"fmt"
)

type Dependencies struct {
	NewVerifyPrefectureCityUseCase NewVerifyPrefectureCityUseCaseFunc
	NewSearchCommutingAreasUseCase NewSearchCommutingAreasUseCaseFunc
	NewSearchByKeywordUseCase      NewSearchByKeywordUseCaseFunc
}

type Module struct {
	handler routeHandler
}

func NewModule(deps Dependencies) (*Module, error) {
	if deps.NewVerifyPrefectureCityUseCase == nil {
		return nil, fmt.Errorf("new verify prefecture city usecase factory is required")
	}
	if deps.NewSearchCommutingAreasUseCase == nil {
		return nil, fmt.Errorf("new search commuting areas usecase factory is required")
	}
	if deps.NewSearchByKeywordUseCase == nil {
		return nil, fmt.Errorf("new search by keyword usecase factory is required")
	}
	// Capture app-lifetime dependencies at module construction.
	// Handlers are reused, while use cases are created per request via injected factories.
	return &Module{
		handler: NewHandler(
			deps.NewVerifyPrefectureCityUseCase,
			deps.NewSearchCommutingAreasUseCase,
			deps.NewSearchByKeywordUseCase,
		),
	}, nil
}

func (m *Module) Handler() routeHandler {
	if m == nil {
		return nil
	}
	return m.handler
}
