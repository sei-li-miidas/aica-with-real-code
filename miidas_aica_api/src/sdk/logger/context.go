package logger

import (
	"io"

	"github.com/rs/zerolog"

	"aica/api/sdk/slice"
)

type (
	// BatchContext はバッチ用ログ環境です。
	BatchContext interface {
		NewLogger(jobID string) LevelLogger
	}

	// ApiContext はAPI用ログ環境です。
	ApiContext interface {
		// NewRequestLogger httpリクエスト用のロガーを作ります。
		NewRequestLogger(...string) LevelLogger

		// NewApiLogger http全体で使うロガーを作ります。
		NewApiLogger() LevelLogger
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

// NewBatchContext はバッチ用のロガーの環境を作成します。
func NewBatchContext(configures ...Configure) BatchContext {
	return newContext(configures...)
}

// NewApiContext はAPI用のロガーの環境を作成します。
func NewApiContext(category string, configures ...Configure) ApiContext {
	return newContext(append(configures, Category(category))...)
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

// NewLogger ロガーを作成します。
func (ctx context) NewLogger(jobID string) LevelLogger {
	return levelLogger{
		logger: ctx.baseLogger.With().Str("job_id", jobID).Logger(),
	}
}

// NewApiLogger はApiで使うロガーを作成します。
// このロガーはapiの開始、終了などリクエストとは関係ないところで使います。
func (ctx context) NewApiLogger() LevelLogger {
	return levelLogger{
		logger: ctx.baseLogger,
	}
}

/*
httpのみ前提だったので、一旦コメントアウト。
// NewRequestLogger はhttpリクエスト用のロガーを作成します。
func (ctx context) NewRequestLogger(sesKey, sessionID, reqKey, requestID string) LevelLogger {
	return levelLogger{
		logger: ctx.baseLogger.With().Str(sesKey, sessionID).Str(reqKey, requestID).Logger(),
	}
}
*/

// NewRequestLogger はhttpリクエスト用のロガーを作成します。
func (ctx context) NewRequestLogger(keyValues ...string) LevelLogger {
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
