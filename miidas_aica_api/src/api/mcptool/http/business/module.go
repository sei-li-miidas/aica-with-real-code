package business

import (
	"fmt"
)

type Dependencies struct {
	NewGetDetailUseCase NewGetDetailUseCaseFunc
}

type Module struct {
	handler routeHandler
}

func NewModule(deps Dependencies) (*Module, error) {
	if deps.NewGetDetailUseCase == nil {
		return nil, fmt.Errorf("new get detail usecase factory is required")
	}
	return &Module{
		handler: NewHandler(deps.NewGetDetailUseCase),
	}, nil
}

func (m *Module) Handler() routeHandler {
	if m == nil {
		return nil
	}
	return m.handler
}
