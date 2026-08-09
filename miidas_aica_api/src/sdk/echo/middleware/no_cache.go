package middleware

import (
	"github.com/labstack/echo/v4"

	"aica/api/sdk/http"
)

type (
	NoCacheBuilder interface {
		Builder
	}

	nocacheBuilder struct {
	}
)

func NoCache() NoCacheBuilder {
	return &nocacheBuilder{}
}

func (n nocacheBuilder) Build() echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			c.Response().Header().Set(http.HeaderCacheControl, "no-cache, no-store, must-revalidate, private")
			c.Response().Header().Set(http.HeaderPragma, "no-cache")
			return next(c)
		}
	}
}
