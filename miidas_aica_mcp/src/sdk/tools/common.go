package tools

import (
	"aica/mcp/sdk/debug"
	mlogger "aica/mcp/sdk/logger"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"slices"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/mark3labs/mcp-go/mcp"
)

const (
	InternalToolNamePrefix = "internal_tool_"
	distance               = 1
	limit                  = 10
	minNatureScore         = 3
	minJobTypeScore        = 0.4
	messageToLLMKey        = "MessageToLLM"
	errorMessageKey        = "Message"
)

// httpClient is a shared HTTP client with timeout to prevent requests from hanging indefinitely
var httpClient = &http.Client{
	Timeout: 30 * time.Second,
}

func NewCallToolResult(messageKey string, messageContent string) *mcp.CallToolResult {
	result := map[string]string{
		messageKey: messageContent,
	}

	jsonBytes, err := json.Marshal(result)
	if err != nil {
		// 基本ないはず
		return mcp.NewToolResultError(messageContent)
	}

	// OpenAI Agent SDKの仕様かと思って、NewToolResultErrorを返した場合、Exceptionが発生します。
	// なので、NewToolResultErrorをやめて、CallToolResultを使います。
	// ツール実行結果にMessageが入っている場合、Agentサーバの方はツール実行失敗とみなします。
	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.NewTextContent(string(jsonBytes)),
		},
	}
}

func NewErrorCallToolResult(messageContent string) *mcp.CallToolResult {
	return NewCallToolResult(errorMessageKey, messageContent)
}

func NewErrorCallToolResultInvalidArgument(argumentName string) *mcp.CallToolResult {
	return NewErrorCallToolResult(fmt.Sprintf("引数\"%s\"の値は無効なので、ユーザーに確認してください。", argumentName))
}

func NewErrorCallToolResultInvalidSessionID() *mcp.CallToolResult {
	return NewErrorCallToolResult("引数\"SessionID\"が無効な値です。SessionIDは一番最初のメッセージに必ず含まれているので、そこから引用してください。")
}

func NewCallToolResultMessageToLLM(message string) *mcp.CallToolResult {
	return NewCallToolResult(messageToLLMKey, message)
}

func newPostRequest(traceInfo commonRequest, url string, payload any) (*http.Request, error) {
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, err
	}

	req.Header = http.Header{
		"X-SESSION-ID": {traceInfo.SessionID},
		"X-REQUEST-ID": {traceInfo.RequestID},
		"Content-Type": {"application/json"},
	}

	return req, nil
}

func executeSearchJobPostingsRequest(logger mlogger.LevelLogger, toolName string, traceInfo commonRequest, url string, payload any) *mcp.CallToolResult {
	debug.Log(toolName, "url", url)

	req, err := newPostRequest(traceInfo, url, payload)
	if err != nil {
		logger.Error("newPostRequestが失敗しました。", "tool", toolName, "url", url, "payload", payload, "error", err)
		return NewErrorCallToolResult(err.Error())
	}

	resp, err := httpClient.Do(req)
	if err != nil {
		logger.Error("APIリクエストが失敗しました。", "tool", toolName, "url", url, "payload", payload, "error", err)
		return NewErrorCallToolResult(err.Error())
	}
	defer func() {
		_ = resp.Body.Close()
	}()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusBadRequest {
		logger.Error("APIリクエストが失敗しました。", "tool", toolName, "url", url, "payload", payload, "status", resp.Status)
		return NewErrorCallToolResult(fmt.Sprintf("APIリクエストが失敗しました: %s", resp.Status))
	}

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		logger.Error("レスポンス解析が失敗しました。", "tool", toolName, "url", url, "payload", payload, "data", bodyBytes, "error", err)
		return NewErrorCallToolResult(err.Error())
	}

	return &mcp.CallToolResult{
		Content: []mcp.Content{
			mcp.NewTextContent(string(bodyBytes)),
		},
		IsError: resp.StatusCode == http.StatusBadRequest,
	}
}

func initializeTool(toolName string, traceInfo *commonRequest) (mlogger.LevelLogger, *mcp.CallToolResult) {
	logger := mlogger.GetMCPContext().NewToolLogger("SessionID", traceInfo.SessionID, "RequestID", traceInfo.RequestID)
	logger.Info("トレースログ", "tool", toolName, "parameters", traceInfo)

	if len(traceInfo.SessionID) == 0 {
		return logger, NewErrorCallToolResultInvalidSessionID()
	}

	if len(traceInfo.RequestID) == 0 {
		traceInfo.RequestID = uuid.NewString()
	}

	return logger, nil
}

// 空文字列判定
func isBlankString(s string) bool {
	return len(strings.TrimSpace(s)) == 0
}

// ポインタ版の空文字列判定
func isBlankPtrString(ptr *string) bool {
	if ptr == nil {
		return true
	}
	return isBlankString(*ptr)
}

// ポインタ版の負の整数判定
func isNegativePtrInt(ptr *int) bool {
	if ptr == nil {
		return false
	}
	return *ptr < 0
}

// ポインタ版の有効値判定
func ptrStringNotIn(ptr *string, valids []string) bool {
	if isBlankPtrString(ptr) {
		// 設定されていない場合、有効とみなす
		return false
	}
	return !slices.Contains(valids, *ptr)
}
