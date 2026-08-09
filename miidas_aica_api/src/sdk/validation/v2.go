package validation

import (
	merr "aica/api/sdk/error"

	v2 "github.com/go-playground/validator/v10"
	v1 "gopkg.in/validator.v2"
)

type (
	v1Validator v1.ValidationFunc
)

// ConvertValidateResult バリデーションライブラリごとに指定された返り値に変換する。
// カスタムバリデーター側はそれぞれのエラーケースに応じたエラーを返却する。
// 現行のバリデーターライブラリではカスタム貼りデーターの返り値がbool指定なので、nilならtrue,エラーならfalseになるようにしている。
func ConvertValidateResult(validator v1Validator) v2.Func {
	return func(fl v2.FieldLevel) bool {
		return validator(fl.Field().Interface(), fl.Param()) == nil
	}
}

// CreateMiidasErrorFromValidationError バリデーターのエラーをaica/api/sdkのエラーに変換する。(validateV2用)
func CreateMiidasErrorFromValidationError(e v2.FieldError) merr.FieldValidationError {
	var createdError merr.FieldValidationError
	switch e.Tag() {
	default:
		createdError = merr.ErrUnknown
	}
	return createdError
}
