package middleware

import (
	"net/http"
	"reflect"

	"github.com/labstack/echo/v4"

	"aica/api/sdk/debug"
	mectx "aica/api/sdk/echo/context"
)

// CustomValidator はリクエスト固有のスタムバリデーターです。
// validateタグでまかなえないものを定義します。
type CustomValidator func(param any) error

// nopValidator は何もしないカスタムバリデーター
func nopValidator(_ any) error {
	return nil
}

// BinderBuilder はBinderミドルウェアを作成するbuilderパターンのインタフェース
type BinderBuilder interface {
	Builder
	// TODO: 今利用されていないですが、今後使うかもなので、いったんそのままにしています。
	// カスタムバリデーターの設定
	Validator(CustomValidator) BinderBuilder
}

type binderBuilder struct {
	DecodedType     reflect.Type
	CustomValidator CustomValidator
}

// Binder はリクエストのBindミドルウエアを作成します。
func Binder(p any) BinderBuilder {
	return &binderBuilder{
		DecodedType:     reflect.TypeOf(p),
		CustomValidator: nopValidator,
	}
}

func (b *binderBuilder) Validator(v CustomValidator) BinderBuilder {
	if v == nil {
		return b
	}
	b.CustomValidator = v
	return b
}

func (b binderBuilder) Build() echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			v, err := func() (any, error) {
				if b.DecodedType == nil {
					return nil, nil
				}
				v, err := bind(c, b.DecodedType)
				if err != nil {
					return nil, err
				}
				if err := c.Validate(v); err != nil {
					return v, err
				}
				return v, b.CustomValidator(v)
			}()
			if err != nil {
				return err
			}

			mectx.SetBoundParam(c, v)

			return next(c)
		}
	}
}

func bind(c echo.Context, t reflect.Type) (any, error) {
	v := reflect.New(t).Interface()

	if err := c.Bind(v); err != nil {
		debug.Log("bind error", "error", err)
		return nil, echo.NewHTTPError(http.StatusBadRequest)
	}

	return v, nil
}
