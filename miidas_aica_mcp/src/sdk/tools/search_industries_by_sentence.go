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

type (
	toolSearchIndustriesBySentence struct {
		name string
	}

	SearchSemanticIndustryRequest struct {
		Sentence string
		Provider *string
		Distance *float64
		Limit    *int
	}
)

func newToolSearchIndustriesBySentence() *toolSearchIndustriesBySentence {
	return &toolSearchIndustriesBySentence{name: "search_industries_by_sentence"}
}

func (t toolSearchIndustriesBySentence) getName() string {
	return t.name
}

func (t toolSearchIndustriesBySentence) createToolHandler(apiServer string, getProvider func() string) server.ToolHandlerFunc {

	// create TypedHandlerFunc
	handler := func(ctx context.Context, request mcp.CallToolRequest, args searchIndustriesBySentenceRequest) (*mcp.CallToolResult, error) {
		logger, errorToolResult := initializeTool(t.name, &args.commonRequest)
		if errorToolResult != nil {
			return errorToolResult, nil
		}

		if len(args.Sentence) == 0 {
			return NewErrorCallToolResultInvalidArgument("Sentence"), nil
		}

		p := getProvider()
		d := float64(distance)
		l := int(limit)

		payload := SearchSemanticIndustryRequest{
			Provider: &p,
			Sentence: args.Sentence,
			Distance: &d,
			Limit:    &l,
		}

		url := fmt.Sprintf("%s/aica/mcptool/industry/search/semantic", apiServer)
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

		var data []industry
		if err := json.NewDecoder(resp.Body).Decode(&data); err != nil {
			logger.Error("レスポンス解析が失敗しました。", "tool", t.name, "url", url, "payload", payload, "error", err)
			return NewErrorCallToolResult(err.Error()), nil
		}

		debug.Log(t.name, "Response data", data)

		if len(data) == 0 {
			return NewCallToolResultMessageToLLM("該当する業種が見つかりませんでした。"), nil
		}

		industryResults := make([]map[string]string, len(data))
		for i, item := range data {
			industryResults[i] = map[string]string{
				"業種名":  item.Name,
				"業種説明": item.Description,
			}
		}

		content, err := json.Marshal(map[string]any{
			"業種一覧": industryResults,
		})
		if err != nil {
			logger.Error("ツール結果生成が失敗しました。", "tool", t.name, "url", url, "payload", payload, "industryResults", industryResults, "error", err)
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

// Deprecated: This function is deprecated.
func init() {
	tool := newToolSearchIndustriesBySentence()
	addToolHandler(tool)
}
