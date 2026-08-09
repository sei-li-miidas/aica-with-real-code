package main

import (
	"aica/api/sdk/aica"
	"aica/api/sdk/debug"
	mecho "aica/api/sdk/echo"
	mhttp "aica/api/sdk/http"
	mlogger "aica/api/sdk/logger"
	"os"
)

var (
	serviceDef  = aica.MCPToolAPI
	logCategory = serviceDef.LogCategory
	serviceName = serviceDef.DBEnv
)

func main() {
	cfg := parseFlags()

	// 初期化
	debug.SetupLogger(cfg.debugMode, cfg.category)
	logCtx := mlogger.NewApiContext(cfg.category, mlogger.NeedCaller(cfg.debugMode))
	logger := logCtx.NewApiLogger()

	logger.Info("let's start setup")
	var err error
	cfg.port, err = resolvePort(logger)
	if err != nil {
		logger.Error("can't resolve port", "err", err)
		os.Exit(mhttp.ExitStatusInit)
	}

	logger.Info("setup configurations",
		"show-routes", cfg.showRoute,
		"category", cfg.category,
		"port", cfg.port,
		"debug", cfg.debugMode)

	setupInfrastructure(logger, cfg)
	defer teardownInfrastructure(logger)

	server := setupServer(logger, logCtx, cfg.port)
	root := server.Group(mhttp.MCPTOOL_ROUTE_PREFIX)
	mecho.SetupDefaultRoute(root)
	setupRoutes(root, logger, setupRoutesOptionsForBuild())

	if cfg.showRoute {
		mecho.PrintRoute(server)
	}

	logger.Info("all setup success. start server.")
	if err := mecho.Start(server); err != nil {
		logger.Error("can't start server", "err", err)
	}
}
