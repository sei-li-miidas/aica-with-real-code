package echo

import (
	mhttp "aica/api/sdk/http"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/labstack/echo/v4"
	"gopkg.in/tylerb/graceful.v1"

	"aica/api/sdk/validation"
)

const (
	gracefulTimeout = 5 * time.Second
)

type (
	// RouteRegisterFunc はechoのroute定義関数
	RouteRegisterFunc func(RouteRegister)
)

// NewDefaultServer は初期設定済みのサーバーを作成します。
func NewDefaultServer(port int) *echo.Echo {
	e := echo.New()
	e.HTTPErrorHandler = ErrorHandler
	e.Validator = defaultValidator
	e.Server.Addr = fmt.Sprintf(":%d", port)
	return e
}

// Start はサーバーをスタートします。
func Start(e *echo.Echo) error {
	return graceful.ListenAndServe(e.Server, gracefulTimeout)
}

// PrintRoute はルート定義を出力します。
func PrintRoute(e *echo.Echo) {
	data, err := json.MarshalIndent(e.Routes(), "", "    ")
	if err != nil {
		fmt.Printf("%+v\r", err)
	} else {
		fmt.Println(string(data))
	}
}

var (
	// デフォルトのPreMiddleware
	defaultPreMiddlewares = []echo.MiddlewareFunc{}

	// デフォルトのPostMiddleware
	// defaultPostMiddlewares = []echo.MiddlewareFunc{
	// 	memw.Recoverer().Build(),
	// 	middleware.Gzip(),
	// 	memw.NoCache().Build(),
	// 	middleware.RequestID(),
	// 	memw.RequestIDSetter(),
	// }

	// デフォルトのルート
	defaultRouteRegister = []RouteRegisterFunc{
		func(e RouteRegister) {
			e.GET(mhttp.MCPTOOL_HEALTH_ROUTE, func(c echo.Context) error {
				return c.NoContent(http.StatusOK)
			})
		},
	}

	// デフォルトのバリデーター
	defaultValidator = Validator{
		V: func(p any) error {
			if errs := validation.ValidateStruct(p); errs == nil || errs.Valid() {
				if errsV2 := validation.ValidateStructV2(p); errsV2 != nil {
					return errsV2
				}
				return nil
			} else {
				return errs
			}
		},
	}
)

// SetupDefaultPreMiddleware はデフォルトのPreMiddlewareを設定します。
func SetupDefaultPreMiddleware(e *echo.Echo) {
	for _, mw := range defaultPreMiddlewares {
		e.Pre(mw)
	}
}

// SetupDefaultPostMiddleware はデフォルトのPostMiddlewareを設定します。
// func SetupDefaultPostMiddleware(e RouteRegister) {
// 	for _, mw := range defaultPostMiddlewares {
// 		e.Use(mw)
// 	}
// }

// SetupDefaultRoute はデフォルトのルートを設定します。
// 現段階では/healthだけです。
func SetupDefaultRoute(e RouteRegister) {
	for _, rr := range defaultRouteRegister {
		rr(e)
	}
}

// Validator はecho.Validatorの実体です。
type Validator struct {
	V func(any) error
}

func (v Validator) Validate(p any) error {
	return v.V(p)
}
