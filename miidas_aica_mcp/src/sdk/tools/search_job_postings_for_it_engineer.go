package tools

import (
	"context"
	"fmt"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolSearchJobPostingsForITEngineer struct {
	name string
}

func newToolSearchJobPostingsForITEngineer() *toolSearchJobPostingsForITEngineer {
	return &toolSearchJobPostingsForITEngineer{name: "search_job_postings_for_it_engineer"}
}

func (t toolSearchJobPostingsForITEngineer) getName() string {
	return t.name
}

func (t toolSearchJobPostingsForITEngineer) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {
	// create TypedHandlerFunc
	handler := func(ctx context.Context,
		request mcp.CallToolRequest,
		args itEngineerPositionSearchParams) (*mcp.CallToolResult, error,
	) {
		logger, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		url := fmt.Sprintf("%s/aica/mcptool/positions/search/it_engineer", apiServer)
		return executeSearchJobPostingsRequest(logger, t.name, args.commonRequest, url, args), nil
	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolSearchJobPostingsForITEngineer()
	addToolHandler(tool)
}
