package debug

import (
	"io"

	mlogger "aica/api/sdk/logger"
)

var (
	logFunc func(string, ...any)
)

func init() {
	// SetupLoggerを実行しないと何も出力されない
	logFunc = nopLog
}

// SetupLogger はデバッグ用ロガーを設定します。
func SetupLogger(need bool, category string) {
	setupLogger(mlogger.DefaultWriter(), need, category)
}

// setupLogger はデバッグ用ロガーの設定の内部処理です。
//
// need引数はデバックログを出力するためのフラグと、callerを出すフラグの両方を兼ねています。
// デバッグログが必要なときはcallerも必要なので。
func setupLogger(w io.Writer, need bool, category string) {
	configures := []mlogger.Configure{}
	configures = append(configures, mlogger.Writer(w), mlogger.NeedCaller(need), mlogger.DebugSkipFrameCount())

	ctx := mlogger.NewDebugContext(category, configures...)
	l := ctx.NewDebugLogger()
	logFunc = l.Log
}

// Log はログ出力します。
// 常にdebugレベルです。
func Log(msg string, keyvals ...any) {
	logFunc(msg, keyvals...)
}

// nopLog はデバッグログを出力しないときの関数です
func nopLog(string, ...any) {
	// nop
}
