package middleware

import (
	"errors"
	"fmt"

	mectx "aica/api/sdk/echo/context"
	mhttp "aica/api/sdk/http"
	"aica/api/sdk/logger"

	"github.com/labstack/echo/v4"
)

var (
	ErrRequestMiddlewareNotUsed = errors.New("echo request_id middleware not used") // RequestIDミドルウェアが準備されていないときのエラー
)

// RequestLoggerBuilder はリクエストID付きロガーを準備するミドルウェアビルダー
type RequestLoggerBuilder interface {
	Builder
}

type requestLoggerBuilder struct {
	ctx logger.ApiContext
}

// RequestLogger はコンストラクタ
func RequestLogger(ctx logger.ApiContext) RequestLoggerBuilder {
	return &requestLoggerBuilder{
		ctx: ctx,
	}
}

func (b requestLoggerBuilder) Build() echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			if lctx := b.ctx; lctx != nil {
				sID := c.Request().Header.Get("X-SESSION-ID")
				if rID := c.Request().Header.Get("X-REQUEST-ID"); rID != "" {
					l := lctx.NewRequestLogger("session_id", sID, "request_id", rID, "method", c.Request().Method, "path", c.Request().RequestURI)
					mectx.SetLogger(c, l)
				} else {
					// 一応何か出してあげるが、警告をだしておく
					l := lctx.NewRequestLogger("session_id", sID, "request_id", "DUMMY", "method", c.Request().Method, "path", c.Request().RequestURI)
					if c.Request().RequestURI != fmt.Sprintf("%s%s", mhttp.MCPTOOL_ROUTE_PREFIX, mhttp.MCPTOOL_HEALTH_ROUTE) {
						l.Warn(ErrRequestMiddlewareNotUsed.Error())
					}
					mectx.SetLogger(c, l)
				}
			}
			return next(c)
		}
	}
}
