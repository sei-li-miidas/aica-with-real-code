package logger

import (
	"io"

	"github.com/rs/zerolog"

	"aica/mcp/sdk/slice"
)

type (
	// MCPContext はMCP用ログ環境です。
	MCPContext interface {
		// NewToolLogger  ツールリクエスト用のロガーを作ります。
		NewToolLogger(...string) LevelLogger

		// NewMCPLogger MCP全体で使うロガーを作ります。
		NewMCPLogger() LevelLogger
	}

	// DebugContext はデバッグ用ログ環境です。
	DebugContext interface {
		NewDebugLogger() DebugLogger
	}

	// context はロガーの環境の実体です。
	context struct {
		baseLogger zerolog.Logger
	}
)

const (
	debugLogSkipFrameCount  = 5 // デバッグログのときにスキップするフレーム数
	normalLogSkipFrameCount = 4 // 通常のログのときするスキップするフレーム数
)

var (
	defaultConfig = Config{
		NeedCaller:               false,
		OutputLevel:              zerolog.InfoLevel,
		Writer:                   DefaultWriter(),
		CallerWithSkipFrameCount: normalLogSkipFrameCount,
	}

	mcpContext *context
)

// NeedCaller は呼び出し元を追加する
func NeedCaller(need bool) Configure {
	return func(c *Config) {
		c.NeedCaller = need
	}
}

func Category(category string) Configure {
	return func(c *Config) {
		c.Category = category
	}
}

func Writer(w io.Writer) Configure {
	return func(c *Config) {
		c.Writer = w
	}
}

// skipFrameCount は呼び出し元を追加するときにスキップするフレームカウントを設定します。
func skipFrameCount(frameCount int) Configure {
	return func(c *Config) {
		c.CallerWithSkipFrameCount = frameCount
	}
}

// NormalSkipFrameCount は通常ログのときにスキップするフレーム数
func NormalSkipFrameCount() Configure {
	return skipFrameCount(normalLogSkipFrameCount)
}

// DebugSkipFrameCount はデバッグログのときにスキップするフレーム数
func DebugSkipFrameCount() Configure {
	return skipFrameCount(debugLogSkipFrameCount)
}

// MCPContext はMCP用のロガーの環境を作成します。
func NewMCPContext(category string, configures ...Configure) MCPContext {
	mcpContext = newContext(append(configures, Category(category))...)
	return mcpContext
}

func NewDebugContext(category string, configures ...Configure) DebugContext {
	return newDebugContext(append(configures, Category(category))...)
}

func newContext(configures ...Configure) *context {
	cfg := configuration(configures...)
	return &context{
		baseLogger: newZeroLogger(cfg),
	}
}

func newDebugContext(configures ...Configure) *context {
	cfg := configuration(configures...)
	return &context{
		baseLogger: newDebugLogger(cfg),
	}
}

func configuration(configures ...Configure) Config {
	cfg := defaultConfig
	for _, c := range configures {
		c(&cfg)
	}
	return cfg
}

// NewMCPLogger はMCPで使うロガーを作成します。
// このロガーはツール実行とは関係ないところで使います。
func (ctx context) NewMCPLogger() LevelLogger {
	return levelLogger{
		logger: ctx.baseLogger,
	}
}

// NewToolLogger はツール実行時用のロガーを作成します。
func (ctx context) NewToolLogger(keyValues ...string) LevelLogger {
	kvs := make([]string, len(keyValues))
	copy(kvs, keyValues)
	if len(keyValues)%2 != 0 {
		kvs = append(kvs, "ARGUMENTS MUST BE EVEN NUMBERS")
	}

	c := ctx.baseLogger.With()
	for _, idx := range slice.ChunkingIndex(len(kvs), 2) {
		chunk := kvs[idx.L:idx.H]
		c = c.Str(chunk[0], chunk[1])
	}
	return levelLogger{
		logger: c.Logger(),
	}
}

func (ctx context) NewDebugLogger() DebugLogger {
	return debugLogger{
		logger: ctx.baseLogger.With().Logger(),
	}
}

func GetMCPContext() MCPContext {
	return mcpContext
}
