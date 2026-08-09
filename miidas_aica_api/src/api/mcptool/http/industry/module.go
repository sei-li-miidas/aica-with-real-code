package industry

import (
	"fmt"
)

type Dependencies struct {
	NewSemanticUseCase NewSemanticIndustryUseCaseFunc
}

type Module struct {
	handler routeHandler
}

func NewModule(deps Dependencies) (*Module, error) {
	if deps.NewSemanticUseCase == nil {
		return nil, fmt.Errorf("new semantic usecase factory is required")
	}
	return &Module{
		handler: NewHandler(deps.NewSemanticUseCase),
	}, nil
}

func (m *Module) Handler() routeHandler {
	if m == nil {
		return nil
	}
	return m.handler
}
