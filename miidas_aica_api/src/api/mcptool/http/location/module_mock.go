//go:build mock

package location

func NewMockModule(_ Dependencies) (*Module, error) {
	return &Module{
		handler: NewMockHandler(),
	}, nil
}
