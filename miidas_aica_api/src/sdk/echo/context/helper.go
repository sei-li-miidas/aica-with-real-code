/*
echoのContextを扱う関数等を定義します。
*/
package context

import (
	"context"

	"github.com/labstack/echo/v4"
	"github.com/pkg/errors"

	"aica/api/sdk/logger"
)

const (
	keyLogger        = "logger"          // ロガー
	keyBoundParam    = "boundParam"      // Bindされたパラメーター
	keyErrStatusCode = "errorStatusCode" // エラー発生時のhttpステータスコード
)

// Logger はロガーを取得します。
func Logger(c echo.Context) logger.LevelLogger {
	ret := c.Get(keyLogger)
	if ret == nil {
		return nil
	}
	return ret.(logger.LevelLogger)
}

// SetLogger はロガーをセットします
func SetLogger(c echo.Context, logger logger.LevelLogger) {
	c.Set(keyLogger, logger)
}

// RequestID はrequest idを取得します。
// この関数はechoのRequestIDミドルウェア向けです。
func RequestID(c echo.Context) string {
	return c.Response().Header().Get(echo.HeaderXRequestID)
}

// BoundParam はBindされたパラメータを取得します。
func BoundParam(c echo.Context) any {
	if ret := c.Get(keyBoundParam); ret == nil {
		return nil
	} else {
		return ret
	}
}

// SetBoundParam はBindされたパラメータをセットします。
func SetBoundParam(c echo.Context, param any) {
	c.Set(keyBoundParam, param)
}

// ErrorStatusCode はエラー時httpステータスコードを返します。
func ErrorStatusCode(c echo.Context) (int, bool) {
	v := c.Get(keyErrStatusCode)
	if v == nil {
		return 0, false
	}
	return v.(int), true
}

// SetErrorStatusCode はエラー時のhttpステータスコードをセットします。
// コードの内容は特に見てないので注意してください。
func SetErrorStatusCode(c echo.Context, code int) {
	c.Set(keyErrStatusCode, code)
}

// IsContextCanceledByClient クライアントによる通信キャンセルが発生したかを判定する
func IsContextCanceledByClient(c echo.Context, err error) bool {
	req := c.Request()
	if errors.Is(err, context.Canceled) {
		select {
		case <-req.Context().Done():
			return true
		default:
			return false
		}
	}
	return false
}
