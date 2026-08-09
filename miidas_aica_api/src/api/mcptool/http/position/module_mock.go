//go:build mock

package position

import "fmt"

func NewMockModule(deps Dependencies) (*Module, error) {
	if deps.Logger == nil {
		return nil, fmt.Errorf("logger is required")
	}
	return &Module{
		handler: newMockHandler(),
	}, nil
}
