package http

// ポートはローカル環境での動作のため、ユニークな値にすること。
// カテゴリーはログの種類に使われるため、ユニークな値にすること。
import (
	"aica/api/sdk/env"
)

const (
	CategoryMCPTool = "MCP_TOOL_API"
)

var portMap = map[string]int{
	CategoryMCPTool: 10001,
}

// GetApiPort はAPIのlistenポートを取得します。
func GetApiPort(name string) (int, error) {
	p := env.NewPrefixer(env.Prefix, name)
	return p.GetInt("PORT")
}

func DefaultApiPort(name string) (int, bool) {
	value, exists := portMap[name]
	return value, exists
}
