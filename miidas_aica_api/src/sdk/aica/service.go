// Package miidas ミイダスの各種サービスの定数等を管理しています。
/*
LogCategoryのルール

LogCategoryは各サービスが出力するログの category に使われます。
{Type}-{App}{Service} というルールに従ってください。
例：Api-CorpAccount
(一部ルール作成前のものがあります。)

DBUserEnvのルール

DBUserEnvは各サービス毎に定義されたデータベースの接続ユーザー名の環境変数に使われます。

{APP}_{SERVICE}_{TYPE} とぃうルールに従ってください。
例：CORP_ACCOUNT_API
例外はありません。
DBUserEnvは間違った場合はDBに接続できないのでルールのチェックをしていません。

*/
package aica

import (
	"regexp"

	"github.com/pkg/errors"
)

// MCPツールアプリケーション定義
var (
	MCPToolAPI = (&service{
		LogCategory: "Api-MCPTool",
		DBEnv:       "MCP_TOOL_API",
	}).Ensure()

	MCPToolBatch = (&service{
		LogCategory: "Batch-MCPTool",
		DBEnv:       "MCP_TOOL_BATCH",
	}).Ensure()
)

type (
	service struct {
		LogCategory     string
		DBEnv           string
		logCategoryRule func(string) bool
	}
)

// Ensure 定義の正しさを保証する
func (s *service) Ensure() *service {
	s.ensureLogCategory()
	return s
}

// ensureLogCategory ログカテゴリの正しさを保証する
func (s *service) ensureLogCategory() {
	var rule = logCategoryRuleStd
	if s.logCategoryRule != nil {
		rule = s.logCategoryRule
	}
	if !rule(s.LogCategory) {
		panic(errors.Errorf("ログカテゴリ名ルール違反： %s", s.LogCategory))
	}
}

var (
	// ログカテゴリの{Type}-{App}{Service} 形式
	logCategoryRuleStd = regexp.MustCompile(`^(Api|Batch)-MCPTool$`).MatchString
)
