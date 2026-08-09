//go:build mock

package jobtype

func NewMockModule(_ Dependencies) (*Module, error) {
	return &Module{
		handler: NewMockHandler(),
	}, nil
}
