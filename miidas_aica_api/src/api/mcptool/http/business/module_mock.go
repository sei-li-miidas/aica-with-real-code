//go:build mock

package business

func NewMockModule(_ Dependencies) (*Module, error) {
	return &Module{
		handler: NewMockHandler(),
	}, nil
}
