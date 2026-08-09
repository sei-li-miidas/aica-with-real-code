package cli

import (
	merr "aica/api/sdk/error"
)

// ExitCode
//
// 旧StatusCodeです。constの値も同じにしています。
type ExitCode int

const (
	ExitProgress ExitCode = 0 // 処理中（次回続きから処理されることを期待するケース）
	ExitSuccess  ExitCode = 1 // 成功
	ExitError    ExitCode = 2 // エラー
	ExitPanic    ExitCode = 3 // パニック発生
	ExitWarn     ExitCode = 4 // 警告
)

// ResolveExitCode
func ResolveExitCode(panicErr, runErr error, aim, process uint64) ExitCode {
	switch {
	case panicErr != nil:
		return ExitPanic
	case runErr != nil:
		if _, isContinuable := merr.IsContinuable(runErr); isContinuable {
			return ExitWarn
		}
		return ExitError
	case aim != process:
		return ExitWarn
	default:
		return ExitSuccess
	}
}

func ResolveExitCodeForWorker(err error, done bool) ExitCode {
	switch {
	case err != nil:
		if _, isContinuable := merr.IsContinuable(err); isContinuable {
			return ExitWarn
		}
		return ExitError
	case !done:
		return ExitProgress
	default:
		return ExitSuccess
	}
}
