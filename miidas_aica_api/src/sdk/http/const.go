package http

// http headers
const (
	HeaderCacheControl = "Cache-Control"
	HeaderPragma       = "Pragma"
)

// api exit codes
const (
	ExitStatusInit = 1 // 初期化失敗
)

// VectorSearchParamsのデフォルト
const (
	DEFAULT_DISTANCE float64 = 0.8 // 類似度（0.0が最もちかい）
)

const (
	INDUSTRY_JOBTYPE_SEARCH_DEFAULT_LIMIT uint = 10 // 職種、業種検索Limit
	POSITION_SEARCH_DEFAULT_LIMIT         uint = 5  //ポジション検索Limit
)

const (
	MCPTOOL_ROUTE_PREFIX = "/aica/mcptool"
	MCPTOOL_HEALTH_ROUTE = "/health"
)

// Custom HTTP status codes
const (
	StatusClientClosedRequest = 499 // クライアントによる通信キャンセル。nginxの定義を流用
)
