//go:build mock

package company

func NewMockModule(_ Dependencies) (*Module, error) {
	return &Module{
		handler: NewMockHandler(),
	}, nil
}
