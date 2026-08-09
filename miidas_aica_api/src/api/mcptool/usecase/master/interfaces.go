package master

import "context"

type masterProvider interface {
	Get(ctx context.Context, name string) (any, error)
}
