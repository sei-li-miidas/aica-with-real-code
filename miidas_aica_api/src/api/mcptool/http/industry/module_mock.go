//go:build mock

package industry

func NewMockModule(_ Dependencies) (*Module, error) {
	return &Module{
		handler: NewMockHandler(),
	}, nil
}
