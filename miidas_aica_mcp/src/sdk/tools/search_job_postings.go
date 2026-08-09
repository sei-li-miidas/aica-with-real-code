package tools

import (
	"context"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolSearchJobPosting struct {
	name string
}

func newToolSearchJobPosting() *toolSearchJobPosting {
	// ミイダス社内では求人のことをPositionと言うが
	// MCPでは求人の英語表記をJob Postingで統一
	return &toolSearchJobPosting{name: "search_job_postings"}
}

func (t toolSearchJobPosting) getName() string {
	return t.name
}

func (t toolSearchJobPosting) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {
	// create TypedHandlerFunc
	handler := func(ctx context.Context,
		request mcp.CallToolRequest,
		args genericPositionSearchParams) (*mcp.CallToolResult, error,
	) {
		logger, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		url := fmt.Sprintf("%s/aica/mcptool/positions/search", apiServer)
		return executeSearchJobPostingsRequest(logger, t.name, args.commonRequest, url, args), nil
	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolSearchJobPosting()
	addToolHandler(tool)
}
