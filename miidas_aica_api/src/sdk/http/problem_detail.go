/*
problem detailはrfc7807で標準化が進められているapiのエラー時のレスポンスを元にしています。

参考：https://tools.ietf.org/html/rfc7807
*/
package http

import (
	"encoding/json"
	"net/http"

	"github.com/labstack/echo/v4"

	merr "aica/api/sdk/error"
)

// problemType は問題の種類です
type problemType string

const (
	problemTypeStructValidation problemType = "StructValidation" // 構造体バリデーションタイプ
	problemTypeFieldValidation  problemType = "FieldValidation"  // 単項目バリデーションタイプ
	problemTypeHTTP             problemType = "HTTP"             // HTTPタイプ
	problemTypeApplication      problemType = "Application"      // アプリケーションエラー
	problemTypeUnknown          problemType = "Unknown"          // 不明
)

type (
	// problemDetail はrfc7807で定義されているapiのエラーレスポンスのミイダス向け最小セットです。
	// この型を埋め込んで各エラーの型を作ります。
	problemDetail struct {
		Type  problemType
		Title string
	}

	// StructValidationProblem はstructのバリデーションエラーのProblemDetail
	StructValidationProblem struct {
		problemDetail
		Details []*fieldValidationProblemInner
	}

	// FieldValidationProblem は単項目のバリデーションエラーのProblemDetail
	FieldValidationProblem struct {
		problemDetail
		merr.FieldValidationError
	}

	AppErrorProblem struct {
		problemDetail
		merr.Error
	}

	// fieldValidationProblemInner はstructの各項目と単項目のバリデーションエラーの詳細
	fieldValidationProblemInner struct {
		Field string
		merr.FieldValidationError
	}

	// EchoHTTPProblem はechoのHTTPErrorに対応するProblemDetail
	EchoHTTPProblem struct {
		problemDetail
		Message string `json:"Message,omitempty"`
	}

	// UnknownProblem はアプリケーションで捕捉できないエラーに対応するProblemDetail
	UnknownProblem struct {
		problemDetail
		Message string
	}
)

func (p FieldValidationProblem) MarshalJSON() ([]byte, error) {
	var inner struct {
		Type    string
		Title   string
		Code    int
		Message string
	}
	inner.Type = string(p.problemDetail.Type)
	inner.Title = p.Title
	inner.Code = p.Bare().ErrCode()
	inner.Message = p.ErrMessage()
	return json.Marshal(inner)
}

func (p AppErrorProblem) MarshalJSON() ([]byte, error) {
	var inner struct {
		Message string
	}
	inner.Message = p.Error.Error()
	return json.Marshal(inner)
}

// NewStructValidationProblem はStructValidationProblemのコンストラクタ
func NewStructValidationProblem(err merr.StructValidationError) *StructValidationProblem {
	if err == nil {
		return nil
	}
	ret := &StructValidationProblem{
		problemDetail: problemDetail{
			Type:  problemTypeStructValidation,
			Title: "request parameters is not valid",
		},
	}
	for field, fErr := range err.Fields() {
		ret.addDetail(field, fErr)
	}
	return ret
}

func (pd *StructValidationProblem) addDetail(field string, detail merr.FieldValidationError) {
	pd.Details = append(pd.Details, &fieldValidationProblemInner{field, detail})
}

// NewFieldValidationProblem はFieldValidationProblemのコンストラクタ
func NewFieldValidationProblem(err merr.FieldValidationError) *FieldValidationProblem {
	if err == nil {
		return nil
	}
	return &FieldValidationProblem{
		problemDetail: problemDetail{
			Type:  problemTypeFieldValidation,
			Title: "request parameter is not valid",
		},
		FieldValidationError: err,
	}
}

func NewAppErrorProblem(err merr.Error) *AppErrorProblem {
	if err == nil {
		return nil
	}
	return &AppErrorProblem{
		problemDetail: problemDetail{
			Type:  problemTypeApplication,
			Title: err.ErrMessage(),
		},
		Error: err,
	}
}

// NewEchoHTTPProblem はEchoHTTPProblemのコンストラクタ
func NewEchoHTTPProblem(err *echo.HTTPError) *EchoHTTPProblem {
	if err == nil {
		return nil
	}
	ret := &EchoHTTPProblem{
		problemDetail: problemDetail{
			Type:  problemTypeHTTP,
			Title: err.Error(),
		},
	}
	if err.Internal != nil {
		ret.Message = err.Internal.Error()
	}

	return ret
}

// NewUnknownProblem はUnknownProblemのコンストラクタ
func NewUnknownProblem() *UnknownProblem {
	return &UnknownProblem{
		problemDetail: problemDetail{
			Type:  problemTypeUnknown,
			Title: "unknown error",
		},
		Message: http.StatusText(http.StatusInternalServerError),
	}
}
