package mv2

import (
	"context"
	"errors"
	"fmt"
	"sync"

	"google.golang.org/grpc"

	"aica/api/sdk/grpc/client"
	"aica/api/sdk/grpc/conf"
)

var (
	cliConn      *grpc.ClientConn
	setupOnce    sync.Once
	teardownOnce sync.Once
)

func SetupConnection(ctx context.Context, category string) (err error) {
	setupOnce.Do(func() {
		err = setup(ctx, category)
	})
	return err
}

func setup(ctx context.Context, category string) error {
	host, port, insecure, err := conf.GetClientConf(category)
	if err != nil {
		return err
	}

	if conn, err := client.NewInternalClient(ctx,
		client.Hostname(host),
		client.Port(port),
		client.AddDialOptions(client.NewSecureOption(insecure)),
	); err != nil {
		return err
	} else {
		cliConn = conn
	}

	return nil
}

func TeardownConn() (err error) {
	teardownOnce.Do(func() {
		if err = cliConn.Close(); err != nil {
			err = fmt.Errorf("mv gateway TeardownConn err: %w", err)
		}
	})

	return err
}

// clientConnection クライアントコネクションを取得
func clientConnection() *grpc.ClientConn {
	if cliConn == nil {
		panic(errors.New("grpc connection is not initialized"))
	}
	return cliConn
}
