package master

import (
	"aica/api/sdk/logger"
	"context"
)

type (
	GetMastersRequest struct {
		Names []string `query:"Names"`
	}

	Masters struct {
		List []*Master
	}

	Master struct {
		Name   string
		Values any
	}

	GetMasters struct {
		logger   logger.LevelLogger
		provider masterProvider
	}
)

func NewGetMasters(logger logger.LevelLogger, provider masterProvider) *GetMasters {
	return newGetMasters(logger, provider)
}

func newGetMasters(logger logger.LevelLogger, provider masterProvider) *GetMasters {
	return &GetMasters{
		logger:   logger,
		provider: provider,
	}
}

func (u *GetMasters) Execute(ctx context.Context, list *GetMastersRequest) (*Masters, error) {
	ret := make([]*Master, 0, len(list.Names))

	for _, v := range list.Names {
		rows, err := u.provider.Get(ctx, v)
		if err != nil {
			u.logger.Warn("存在しないマスターが指定されました。", "name", v)
			continue
		}
		ret = append(ret, &Master{
			Name:   v,
			Values: rows,
		})
	}

	return &Masters{
		List: ret,
	}, nil
}
