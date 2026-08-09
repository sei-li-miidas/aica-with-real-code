package tools

import (
	"aica/mcp/sdk/debug"
	"context"
	"fmt"
	"slices"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolFormApplication struct {
	name string
}

func newToolFormApplication() *toolFormApplication {
	return &toolFormApplication{name: "form_application"}
}

func (t toolFormApplication) getName() string {
	return t.name
}

func (t toolFormApplication) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {
	// create TypedHandlerFunc
	handler := func(ctx context.Context,
		request mcp.CallToolRequest,
		args applicationParams) (*mcp.CallToolResult, error,
	) {
		_, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		// Validate PositionID (必須かつ正の整数)
		if args.PositionID <= 0 {
			return &mcp.CallToolResult{
				Content: []mcp.Content{
					mcp.NewTextContent("Tool Output:エラー - PositionIDは正の整数である必要があります。有効な求人IDを指定してください。"),
				},
				IsError: true,
			}, nil
		}

		// Validate ApplicationType (必須かつ有効な値)
		if args.ApplicationType == "" {
			return &mcp.CallToolResult{
				Content: []mcp.Content{
					mcp.NewTextContent("Tool Output:エラー - ApplicationTypeが指定されていません。「面接選考」または「カジュアル面談」を指定してください。"),
				},
				IsError: true,
			}, nil
		}
		validTypes := []string{"面接選考", "カジュアル面談"}
		isValid := slices.Contains(validTypes, args.ApplicationType)
		if !isValid {
			return &mcp.CallToolResult{
				Content: []mcp.Content{
					mcp.NewTextContent("Tool Output:エラー - ApplicationTypeの値が無効です。「面接選考」または「カジュアル面談」のいずれかを指定してください。"),
				},
				IsError: true,
			}, nil
		}

		url := fmt.Sprintf("%s/aica/mcptool/application/form", apiServer)
		debug.Log(t.name, "url", url)

		// API呼び出しなしで成功レスポンスを返す
		return NewCallToolResultMessageToLLM("応募フォームに必要な情報を登録してください。"), nil
	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolFormApplication()
	addToolHandler(tool)
}
