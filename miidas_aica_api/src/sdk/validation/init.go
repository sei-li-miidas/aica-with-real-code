package validation

import (
	"errors"

	merr "aica/api/sdk/error"

	v2Validation "github.com/go-playground/validator/v10"
	v1Validation "gopkg.in/validator.v2"
)

var (
	customValidator *v1Validation.Validator
	v2Validator     *v2Validation.Validate
)

func init() {
	customValidator = createValidator()
	changeError()
}

// changeError はバリデーションで返されるエラーを変更します
func changeError() {
	v1Validation.ErrUnsupported = v1Validation.TextErr{Err: merr.ErrUnsupported}
	v1Validation.ErrBadParameter = v1Validation.TextErr{Err: merr.ErrBadParameter}
	v1Validation.ErrUnknownTag = v1Validation.TextErr{Err: merr.ErrUnknownTag}
	v1Validation.ErrInvalid = v1Validation.TextErr{Err: merr.ErrInvalid}
	v1Validation.ErrMin = v1Validation.TextErr{Err: merr.ErrLess}
	v1Validation.ErrMax = v1Validation.TextErr{Err: merr.ErrMore}
	v1Validation.ErrLen = v1Validation.TextErr{Err: merr.ErrLength}
	v1Validation.ErrZeroValue = v1Validation.TextErr{Err: merr.ErrRequired}

	// 以下、使用禁止
	errDoNotUse := v1Validation.TextErr{Err: errors.New("DO NOT USE THIS VALIDATION TAG")}
	v1Validation.ErrRegexp = errDoNotUse // その定義毎にv1Validationを作りましょう
}

// createValidator はバリデーターを変更します。
func createValidator() *v1Validation.Validator {
	v := v1Validation.NewValidator()
	v.SetTag("validate")

	v2Validator = v2Validation.New()
	v2Validator.SetTagName("validateV2")

	return v
}
