package tools

import (
	"context"
	"encoding/json"
	"slices"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

var validWorkflowIDs = []string{
	"job_match_diagnosis",
	"position_change_analyze",
}

type toolStartWorkflow struct {
	name string
}

func newToolStartWorkflow() *toolStartWorkflow {
	return &toolStartWorkflow{name: "start_workflow"}
}

func (t toolStartWorkflow) getName() string {
	return t.name
}

func (t toolStartWorkflow) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {
	handler := func(ctx context.Context, request mcp.CallToolRequest, args startWorkflowRequest) (*mcp.CallToolResult, error) {
		logger, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		if !slices.Contains(validWorkflowIDs, args.WorkflowID) {
			return NewErrorCallToolResultInvalidArgument("WorkflowID"), nil
		}

		content, err := json.Marshal(map[string]any{
			"WorkflowID": args.WorkflowID,
		})
		if err != nil {
			logger.Error("ツール結果生成が失敗しました。", "tool", t.name, "WorkflowID", args.WorkflowID, "error", err)
			return NewErrorCallToolResult(err.Error()), nil
		}

		return &mcp.CallToolResult{
			Content: []mcp.Content{
				mcp.NewTextContent(string(content)),
			},
		}, nil
	}

	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolStartWorkflow()
	addToolHandler(tool)
}
