package middleware

import (
	"fmt"
	"os"
	"runtime/debug"

	"github.com/labstack/echo/v4"
	"github.com/pkg/errors"

	mectx "aica/api/sdk/echo/context"
)

type (
	// RecoverBuilder はRecoverMiddlewareを作成するbuilderパターンのインタフェース
	RecoverBuilder interface {
		Builder
	}

	// StackLogger はstack traceを出力する関数
	StackLogger func(er any)

	recoverBuilder struct {
		loggerGetter func(echo.Context) StackLogger
	}
)

// Recoverer はコンストラクタ
func Recoverer() RecoverBuilder {
	return &recoverBuilder{
		loggerGetter: defaultStackLogger,
	}
}

func (r recoverBuilder) Build() echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) (err error) {
			defer func() {
				if rc := recover(); rc != nil {
					l := r.loggerGetter(c)
					l(rc)
					switch e := rc.(type) {
					case error:
						err = e
					case string:
						err = errors.New(e)
					case fmt.Stringer:
						err = errors.New(e.String())
					default:
						err = fmt.Errorf("%v", e)
					}
				}
			}()

			err = next(c)
			return err
		}
	}
}

// defaultStackLogger はロガーを取得する関数を返します
// 規定のロガーがecho.Contextにセットされていたらそれを使います。
// なかった場合、stderrに出力します。この処理は救済措置です。
func defaultStackLogger(c echo.Context) StackLogger {
	if logger := mectx.Logger(c); logger != nil {
		return func(err any) {
			switch v := err.(type) {
			case error:
				if !mectx.IsContextCanceledByClient(c, v) {
					logger.Error("panicking", "error", errors.WithStack(v))
				}
			default:
				logger.Error("panicking", "cause", v, "stack", debug.Stack())
			}
		}
	} else {
		return func(err any) {
			switch v := err.(type) {
			case error:
				if !mectx.IsContextCanceledByClient(c, v) {
					_, _ = fmt.Fprintf(os.Stderr, "message: panicking, error: %+v\n", errors.WithStack(v))
				}
			default:
				_, _ = fmt.Fprintf(os.Stderr, "message: panicking, error: %s, stack: %s\n", err, debug.Stack())
			}
		}
	}
}
