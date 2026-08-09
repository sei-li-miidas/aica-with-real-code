package validation

import (
	merr "aica/api/sdk/error"
	"errors"
	"reflect"

	newValidation "github.com/go-playground/validator/v10"
	"gopkg.in/validator.v2"
)

// ValidateStruct は構造体をバリデーションし、エラーを返します。
// Validなときはtrue。
func ValidateStruct(params any) merr.StructValidationError {
	err := merr.NewStructValidationError()
	p := reflect.ValueOf(params).Interface()

	result := customValidator.Validate(p)
	if result == nil {
		return nil
	}

	switch r := result.(type) {
	case validator.ErrorMap: // paramsがstructのときの
		for key, errs := range r {
			for _, anErr := range errs {
				err.Add(key, toFieldValidationError(anErr))
			}
		}
	case validator.TextErr: // paramsがstructでないとき。ここには来ないはずだが。
		err.Add("text_error", merr.NewUnknownFieldValidationError(r))
	}

	return err
}

// toFieldValidationError はgopkg.in/validator.v2が返す項目ごとのエラーをFieldValidationErrorに変換する
func toFieldValidationError(err error) merr.FieldValidationError {
	if te, ok := err.(validator.TextErr); !ok {
		return merr.NewUnknownFieldValidationError(err) // 不明なエラー
	} else if ve, ok := te.Err.(merr.FieldValidationError); ok {
		return ve
	} else {
		return merr.NewUnknownFieldValidationError(err) // 不明なエラー
	}
}

// ValidateStructV2 は構造体をバリデーションし、エラーを返します。(新バリデーター用）
func ValidateStructV2(params any) merr.StructValidationError {
	err := merr.NewStructValidationError()
	result := v2Validator.Struct(params)

	if result == nil {
		return nil
	}

	var validationErrors newValidation.ValidationErrors
	errors.As(result, &validationErrors)
	for _, currentV2Error := range validationErrors {
		newValidationError := CreateMiidasErrorFromValidationError(currentV2Error)
		err.Add(currentV2Error.Field(), newValidationError)
	}
	return err
}
