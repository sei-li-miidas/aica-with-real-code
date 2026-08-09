package master

import (
	"fmt"
)

type Dependencies struct {
	NewGetMastersUseCase NewGetMastersUseCaseFunc
}

type Module struct {
	handler routeHandler
}

func NewModule(deps Dependencies) (*Module, error) {
	if deps.NewGetMastersUseCase == nil {
		return nil, fmt.Errorf("new get masters usecase factory is required")
	}
	return &Module{
		handler: NewHandler(deps.NewGetMastersUseCase),
	}, nil
}

func (m *Module) Handler() routeHandler {
	if m == nil {
		return nil
	}
	return m.handler
}
