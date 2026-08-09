package aica

import (
	mlogger "aica/mcp/sdk/logger"
	"aica/mcp/sdk/tools"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	"gorm.io/gorm"
)

const (
	AgentProviderBedrock = "bedrock"
	AgentProviderOpenAI  = "openai"

	serverName    = "aica-server"
	serverVersion = "1.0.0"
)

var (
	mcpServer  *server.MCPServer
	httpServer *server.StreamableHTTPServer
)

type (
	ServerUsecase struct {
		db        *gorm.DB
		port      string
		apiServer string
	}
)

var (
	provider string = AgentProviderOpenAI
)

func GetProvider() string {
	return provider
}

func NewServerUsecase(db *gorm.DB, port string, apiServer string) *ServerUsecase {
	return &ServerUsecase{db: db, port: port, apiServer: apiServer}
}

func (u *ServerUsecase) newMCPServer() {
	mcpServer = server.NewMCPServer(
		serverName,
		serverVersion,
		server.WithPromptCapabilities(true),
		server.WithToolCapabilities(true),
		server.WithLogging(),
	)
}

func (u *ServerUsecase) Start() error {
	logger := mlogger.GetMCPContext().NewMCPLogger()

	u.newMCPServer()

	if err := u.addTools(); err != nil {
		logger.Error("Failed to register MCP tools", "error", err)
		return err
	}

	httpServer = server.NewStreamableHTTPServer(
		mcpServer,
		server.WithEndpointPath("sse"),
		server.WithStateLess(true),
		server.WithHeartbeatInterval(0), // Disable heartbeat for non-persistent connections
	)

	logger.Info("Starting StreamableHTTP server", "port", u.port, "endpoint", "/mcp")
	if err := httpServer.Start(fmt.Sprintf(":%s", u.port)); err != nil {
		logger.Error("Failed to start StreamableHTTP server", "error", err)
		return err
	}

	return nil
}

func (u *ServerUsecase) addTools() error {
	logger := mlogger.GetMCPContext().NewMCPLogger()

	toolDefinitions, err := tools.LoadToolDefinitionsEmbedded()
	if err != nil {
		logger.Error("Failed to load tool definitions", "error", err)
		return err
	}

	err = tools.ValidateToolDefinitionsAgainstHandlers(toolDefinitions)
	if err != nil {
		logger.Error("Tool definitions and handlers mismatch", "error", err)
		return err
	}

	for _, toolDefinition := range toolDefinitions {
		normalizedParameters, err := tools.NormalizeParametersSchema(toolDefinition.Parameters)
		if err != nil {
			logger.Error("Failed to normalize tool parameters", "tool_name", toolDefinition.Name, "error", err)
			return err
		}

		toolSchema := mcp.NewToolWithRawSchema(
			toolDefinition.Name,
			toolDefinition.Description,
			normalizedParameters)

		createToolHandlerFunc, ok := tools.ToolHanders[toolDefinition.Name]
		if !ok {
			err = fmt.Errorf("tool handler not found: %s", toolDefinition.Name)
			logger.Error("Tool handler not found", "tool_name", toolDefinition.Name, "error", err)
			return err
		}
		toolHandler := createToolHandlerFunc(u.apiServer, GetProvider)

		mcpServer.AddTool(
			toolSchema,
			toolHandler,
		)
	}

	return nil
}
