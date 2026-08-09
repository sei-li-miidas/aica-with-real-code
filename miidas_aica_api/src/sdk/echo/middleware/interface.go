package middleware

import (
	"github.com/labstack/echo/v4"
)

// Builder はミドルウェアビルダーのインタフェース
type Builder interface {
	Build() echo.MiddlewareFunc
}
