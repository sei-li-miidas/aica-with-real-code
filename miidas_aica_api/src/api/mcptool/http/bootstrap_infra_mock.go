//go:build mock

package main

import mlogger "aica/api/sdk/logger"

func setupInfrastructure(logger mlogger.LevelLogger, _ appConfig) {
	logger.Info("skip infrastructure setup/teardown in mock mode")
}

func teardownInfrastructure(_ mlogger.LevelLogger) {}
