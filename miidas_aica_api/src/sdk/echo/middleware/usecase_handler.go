package middleware

import (
	"context"
	"errors"
	"net"
	"net/http"
	"strings"
	"syscall"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
	perr "github.com/pkg/errors"

	mectx "aica/api/sdk/echo/context"
	merr "aica/api/sdk/error"
	"aica/api/sdk/grpc"
	mhttp "aica/api/sdk/http"
	"aica/api/sdk/logger"
)

type (
	UseCaseHandlerBuilder interface {
		Builder
		Skipper(skipper middleware.Skipper) UseCaseHandlerBuilder
		AdditionalStartMessage(AdditionalParamGetter) UseCaseHandlerBuilder
	}

	StatusCodeMapper func(merr.ErrCode) (code int, found bool)

	// AdditionalParamGetter はログに追加で出力するパラメータをecho.Contextから取得します。
	//
	// 注意
	// ログはjsonで出力されますが、フィールドはsnake_caseにするルールになっています。
	// 自動では変換されないので、returnするmapのキーはsnake_caseにしてください。
	AdditionalParamGetter func(echo.Context) map[string]interface{}

	useCaseHandlerBuilder struct {
		skipper           middleware.Skipper
		codeMapper        StatusCodeMapper
		addnlStartMessage AdditionalParamGetter
	}
)

func UseCaseHandler(cm StatusCodeMapper) UseCaseHandlerBuilder {
	return &useCaseHandlerBuilder{
		skipper: func(c echo.Context) bool {
			return strings.HasSuffix(c.Request().URL.RequestURI(), "/health")
		},
		codeMapper: cm,
		addnlStartMessage: func(_ echo.Context) map[string]interface{} {
			return map[string]any{}
		},
	}
}

// Skipper usecase開始ログ/usecase終了ログ 用のSkipperを登録します
func (b *useCaseHandlerBuilder) Skipper(sk middleware.Skipper) UseCaseHandlerBuilder {
	b.skipper = sk
	return b
}

// AdditionalStartMessage は開始ログに追加で出力する値を取得する関数をセットします。
func (b *useCaseHandlerBuilder) AdditionalStartMessage(f AdditionalParamGetter) UseCaseHandlerBuilder {
	b.addnlStartMessage = f
	return b
}

func (b useCaseHandlerBuilder) Build() echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			logger := mectx.Logger(c)

			if !b.skipper(c) {
				logger.Info("usecase start")
			}

			var err error
			defer func() {
				var statusCode int
				if err == nil {
					statusCode = resolveNonErrorStatusCode(c)
				} else {
					statusCode = resolveErrorStatusCode(c, err, b.codeMapper, logger)
					warnIfInvalidError(err, logger)
				}

				// 上位のエラーハンドラに調整済みステータスコードを渡すため、コンテキストに保存しておく
				mectx.SetErrorStatusCode(c, statusCode)

				if !b.skipper(c) {
					logger.Info("usecase end")
				}
			}()

			err = next(c)
			return err
		}
	}
}

// resolveNonErrorStatusCode エラーでないときのステータスコードを解決します。
// echoはContextを再利用しますが、そのときの内部のresponseの状態に依存しています。
// 以下の処理を考慮しています。
// 1. Contextが再利用されたとき、ResetメソッドによりStatusCodeが一旦http.StatusOKが設定される。
// 2. レスポンスが完了しているときはCommittedがtrueになる。
func resolveNonErrorStatusCode(c echo.Context) int {
	if c.Response().Committed { // レスポンスに書き込まれているか？
		return c.Response().Status
	}

	return http.StatusInternalServerError
}

func resolveErrorStatusCode(c echo.Context, err error, mapper StatusCodeMapper, l logger.LevelLogger) int {
	var sve merr.StructValidationError
	if errors.As(err, &sve) {
		return http.StatusBadRequest
	}

	var httpErr *echo.HTTPError
	if errors.As(err, &httpErr) {
		return httpErr.Code
	}

	if mectx.IsContextCanceledByClient(c, err) {
		return mhttp.StatusClientClosedRequest
	}

	if grpc.ShouldIgnoreErr(err) {
		return mhttp.StatusClientClosedRequest
	}

	var ne *net.OpError
	if errors.As(err, &ne) {
		if errors.Is(ne.Err, syscall.EPIPE) || errors.Is(ne.Err, syscall.ECONNRESET) {
			// クライアントからのリクエストが切断されて ** いない ** 場合はログを出す
			err := c.Request().Context().Err()
			if !errors.Is(err, context.Canceled) {
				l.Warn("broken pipeが発生しました", "detail", perr.WithStack(ne))
			}

			return http.StatusOK
		}

		l.Error("*net.OpErrorが発生しました", "detail", perr.WithStack(ne))
		return http.StatusInternalServerError
	}

	var ee merr.Error
	if errors.As(err, &ee) {
		switch ee.Type() {
		case merr.FieldValidationErrorType:
			return http.StatusBadRequest
		case merr.AppErrorType:
			code, found := mapper(ee.Bare())
			if !found {
				l.Warn("StatusCodeMapper定義に不備あり", "ErrCode", ee.Bare().ErrCode())
			}

			return code
		}
	}

	return http.StatusInternalServerError
}

func warnIfInvalidError(err error, l logger.LevelLogger) {
	var ee merr.Error
	if errors.As(err, &ee) {
		switch ee.Type() {
		case merr.AppErrorType:
			if errors.Is(err, merr.ErrNilCauseArg) {
				l.Warn("AppError構築に不備あり", "detail", err)
			}
		}
	}
}
