package tools

import (
	"aica/mcp/sdk/debug"
	"context"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolFormRegistration struct {
	name string
}

func newToolFormRegistration() *toolFormRegistration {
	return &toolFormRegistration{name: "form_registration"}
}

func (t toolFormRegistration) getName() string {
	return t.name
}

func (t toolFormRegistration) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {
	// create TypedHandlerFunc
	handler := func(ctx context.Context,
		request mcp.CallToolRequest,
		args registrationParams) (*mcp.CallToolResult, error,
	) {
		_, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		// Validate Registration (必須かつTRUE)
		if !args.Registration {
			return NewErrorCallToolResultInvalidArgument("Registration"), nil
		}

		url := fmt.Sprintf("%s/aica/mcptool/registration/form", apiServer)
		debug.Log(t.name, "url", url)

		// API呼び出しなしで成功レスポンスを返す
		return NewCallToolResultMessageToLLM("登録フォームに必要な情報を登録してください。"), nil
	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolFormRegistration()
	addToolHandler(tool)
}
