package main

import (
	"aica/mcp/internal"
	"aica/mcp/sdk/debug"
	"aica/mcp/sdk/env"
	mlogger "aica/mcp/sdk/logger"
	"aica/mcp/usecase/aica"
	"flag"
)

const (
	defaultPort = "8080"
	serviceName = "MCP"
)

func main() {
	var (
		port      string
		debugMode bool
	)

	flag.BoolVar(&debugMode, "debug", false, "デバッグモード。デバッグログが出力され、全てのログに出力箇所が追加されます。")
	flag.Parse()

	// Logger初期化
	debug.SetupLogger(debugMode, serviceName)
	logCtx := mlogger.NewMCPContext(serviceName, mlogger.NeedCaller(debugMode))
	logger := logCtx.NewMCPLogger()

	logger.Info("Let's start setup")

	// 環境変数読み込み
	logger.Info("Read environment variables --- start")
	prefixer := env.NewPrefixer(env.Prefix, serviceName)
	apiServer := prefixer.MustGet("API_SERVER")
	port, err := prefixer.Get("PORT")
	if err != nil {
		logger.Warn("MCP Server PORT is not set. Use default port")
		port = defaultPort
	}
	logger.Info("Read environment variables --- end")

	// DB初期化
	logger.Info("Setup DB --- start")
	err = internal.SetupMCPDB(serviceName, debugMode, logger)
	if err != nil {
		logger.Fatal("failed to setup db")
		return
	}
	logger.Info("Setup DB --- end")

	// Start the server
	server := aica.NewServerUsecase(internal.MCPDBConnection(), port, apiServer)
	logger.Info("All setup success. Start server.")
	if err := server.Start(); err != nil {
		logger.Fatal("failed to start server", "error", err)
	}
}
