package tools

import (
	"aica/mcp/sdk/debug"
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

type toolSearchOccupationsBySentence struct {
	name string
}

func newToolSearchOccupationsBySentence() *toolSearchOccupationsBySentence {
	return &toolSearchOccupationsBySentence{name: "search_occupations_by_sentence"}
}

func (t toolSearchOccupationsBySentence) getName() string {
	return t.name
}

func (t toolSearchOccupationsBySentence) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {

	// create TypedHandlerFunc
	handler := func(ctx context.Context, request mcp.CallToolRequest, args searchOccupationsBySentenceRequest) (*mcp.CallToolResult, error) {
		logger, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		if len(args.Sentence) == 0 {
			return NewErrorCallToolResultInvalidArgument("Sentence"), nil
		}

		payload := vectorSearchParams{
			Provider: getProvider(),
			Keyword:  args.Sentence,
			Distance: distance,
			Limit:    limit,
		}

		url := fmt.Sprintf("%s/aica/mcptool/jobtype/search/semantic", apiServer)
		debug.Log(t.name, "url", url)

		req, err := newPostRequest(args.commonRequest, url, payload)
		if err != nil {
			logger.Error("newPostRequestが失敗しました。", "tool", t.name, "url", url, "payload", payload, "error", err)
			return NewErrorCallToolResult(err.Error()), nil
		}

		resp, err := httpClient.Do(req)
		if err != nil {
			logger.Error("APIリクエストが失敗しました。", "tool", t.name, "url", url, "payload", payload, "error", err)
			return NewErrorCallToolResult(err.Error()), nil
		}
		defer func() {
			_ = resp.Body.Close()
		}()

		if resp.StatusCode != http.StatusOK {
			logger.Error("APIリクエストが失敗しました。", "tool", t.name, "url", url, "payload", payload, "status", resp.Status)
			return NewErrorCallToolResult(fmt.Sprintf("APIリクエストが失敗しました: %s", resp.Status)), nil
		}

		var data jobtypeSearchSemanticAPIResponse
		if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
			logger.Error("レスポンス解析が失敗しました。", "tool", t.name, "url", url, "payload", payload, "error", err)
			return NewErrorCallToolResult(err.Error()), nil
		}

		debug.Log(t.name, "Response data", data)

		if len(data.Jobtypes) == 0 {
			return NewCallToolResultMessageToLLM("該当する職種が見つかりませんでした。"), nil
		}

		jobTypeResults := make([]map[string]string, len(data.Jobtypes))
		for i, item := range data.Jobtypes {
			jobTypeResults[i] = map[string]string{
				"職種名":  item.Name,
				"職種説明": item.Description,
			}
		}

		content, err := json.Marshal(map[string]any{
			"検索キーワード": data.Keyword,
			"職種":      jobTypeResults,
		})
		if err != nil {
			logger.Error("ツール結果生成が失敗しました。", "tool", t.name, "url", url, "payload", payload, "jobTypeResults", jobTypeResults, "error", err)
			return NewErrorCallToolResult(err.Error()), nil
		}

		return &mcp.CallToolResult{
			Content: []mcp.Content{
				mcp.NewTextContent(string(content)),
			},
		}, nil

	}

	// return server.ToolHandlerFunc
	return mcp.NewTypedToolHandler(handler)
}

func init() {
	tool := newToolSearchOccupationsBySentence()
	addToolHandler(tool)
}
