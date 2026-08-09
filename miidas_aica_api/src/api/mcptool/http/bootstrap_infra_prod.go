//go:build !mock

package main

import (
	"aica/api/api/mcptool/domain/mv2"
	"aica/api/api/mcptool/internal"
	"aica/api/domain/public/master"
	mhttp "aica/api/sdk/http"
	mlogger "aica/api/sdk/logger"
	"context"
	"os"
)

func setupInfrastructure(logger mlogger.LevelLogger, cfg appConfig) {
	logger.Info("setup database connections")
	if err := internal.SetupRDB(serviceName, cfg.category, cfg.debugMode); err != nil {
		logger.Error("setup db connection failed.", "err", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	master.SetupProvider(context.Background(), internal.MasterDBReader, logger)

	if err := mv2.SetupConnection(context.Background(), serviceName); err != nil {
		logger.Error("setup mv2 grpc conn failed.", "detail", err)
		os.Exit(mhttp.ExitStatusInit)
	}
}

func teardownInfrastructure(logger mlogger.LevelLogger) {
	if err := mv2.TeardownConn(); err != nil {
		logger.Error("tear down mv2 grpc conn failed.", "detail", err)
	}
}
