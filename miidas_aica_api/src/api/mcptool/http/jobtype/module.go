package jobtype

import (
	"fmt"
)

type Dependencies struct {
	NewSemanticUseCase NewSemanticJobTypeUseCaseFunc
	NewNatureUseCase   NewNatureJobTypeUseCaseFunc
	NewNameUseCase     NewNameJobTypeUseCaseFunc
}

type Module struct {
	handler routeHandler
}

func NewModule(deps Dependencies) (*Module, error) {
	if deps.NewSemanticUseCase == nil {
		return nil, fmt.Errorf("new semantic usecase factory is required")
	}
	if deps.NewNatureUseCase == nil {
		return nil, fmt.Errorf("new nature usecase factory is required")
	}
	if deps.NewNameUseCase == nil {
		return nil, fmt.Errorf("new name usecase factory is required")
	}
	return &Module{
		handler: NewHandler(deps.NewSemanticUseCase, deps.NewNatureUseCase, deps.NewNameUseCase),
	}, nil
}

func (m *Module) Handler() routeHandler {
	if m == nil {
		return nil
	}
	return m.handler
}
