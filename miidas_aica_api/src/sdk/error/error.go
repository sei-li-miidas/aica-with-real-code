package error

import (
	"errors"
	"fmt"
	"io"
	"runtime"
	"strings"

	perr "github.com/pkg/errors"
)

type (
	// ErrCode はユースケースで返されるエラーの雛形
	ErrCode interface {
		ErrCode() int
	}

	// VariableErrCode はユースケースで返されるエラーの雛形（エラーメッセージは変数が未バインド）
	VariableErrCode interface {
		ErrCode
		BindVariables(...any) ErrCodeMessage
	}

	// ErrCodeMessage はユースケースで返されるエラーの雛形（エラーメッセージ確定済）
	ErrCodeMessage interface {
		ErrCode
		ErrMessage() string
		WithStack() AppError
		WithCause(cause error) AppError
	}

	// Error は汎用的なエラーのインタフェース
	// このインタフェースを実装したエラーはエラーメッセージとしてアプリケーションの外に出ます。
	Error interface {
		Bare() ErrCode
		ErrMessage() string
		Type() string
		error
	}

	// AppError はユースケースで返されるエラー
	AppError interface {
		Error
	}

	variableErrCode struct {
		code          int
		messageFormat string
	}

	errCodeMessage struct {
		code    int
		message string
	}

	appErrorWithStack struct {
		*errCodeMessage
		*stack
	}

	appErrorWithCause struct {
		*appErrorWithStack
		cause error
	}

	stack []uintptr
)

const (
	HTTPType                  = "HTTP"
	AppErrorType              = "AppError"
	StructValidationErrorType = "StructValidationError"
	FieldValidationErrorType  = "FieldValidationError"
)

// errorMessage はエラーのString表現を返す
func errorMessage(err Error) string {
	return fmt.Sprintf("code %d, message %s", err.Bare().ErrCode(), err.ErrMessage())
}

var _ VariableErrCode = (*variableErrCode)(nil)

var _ ErrCodeMessage = (*errCodeMessage)(nil)

var _ AppError = (*appErrorWithStack)(nil)

var _ AppError = (*appErrorWithCause)(nil)

func NewVariableErrCode(code int, messageFormat string) VariableErrCode {
	return &variableErrCode{
		code:          code,
		messageFormat: messageFormat,
	}
}

func (v *variableErrCode) ErrCode() int {
	return v.code
}

func (v *variableErrCode) BindVariables(a ...any) ErrCodeMessage {
	// 簡易的なパラメータ数チェック
	expectedArgs := strings.Count(v.messageFormat, "%") - strings.Count(v.messageFormat, "%%")
	actualArgs := len(a)
	if actualArgs != expectedArgs {
		panic(fmt.Errorf("WRONG NUMBER OF ARGUMENTS: expected %d arguments, but got %d", expectedArgs, actualArgs))
	}

	return &errCodeMessage{
		code:    v.code,
		message: fmt.Sprintf(v.messageFormat, a...),
	}
}

func NewErrCodeMessage(code int, message string) ErrCodeMessage {
	return &errCodeMessage{
		code:    code,
		message: message,
	}
}

func (e *errCodeMessage) ErrCode() int {
	return e.code
}

func (e *errCodeMessage) ErrMessage() string {
	return e.message
}

func (e *errCodeMessage) WithStack() AppError {
	var r AppError = &appErrorWithStack{
		errCodeMessage: e,
		stack:          callers(),
	}
	return r
}

// ErrNilCauseArg AppError構築時にエラー発生時のコンテキスト情報が失われていることを表す
var ErrNilCauseArg = errors.New("CAUSE ARGUMENTS MUST NOT BE NIL")

func (e *errCodeMessage) WithCause(cause error) AppError {
	var r AppError = &appErrorWithCause{
		appErrorWithStack: &appErrorWithStack{
			errCodeMessage: e,
			stack:          callers(),
		},
		cause: cause,
	}
	return r
}

func callers() *stack {
	const depth = 32
	var pcs [depth]uintptr
	n := runtime.Callers(3, pcs[:])
	var st stack = pcs[0:n]
	return &st
}

func (e *appErrorWithStack) Bare() ErrCode {
	return e.errCodeMessage
}

func (e *appErrorWithStack) Type() string {
	return AppErrorType
}

func (e *appErrorWithStack) Error() string {
	return errorMessage(e)
}

func (e *appErrorWithStack) Format(s fmt.State, verb rune) {
	switch verb {
	case 'v':
		if s.Flag('+') {
			_, _ = io.WriteString(s, errorMessage(e))
			e.stack.Format(s, verb)
			return
		}
		fallthrough
	case 's':
		_, _ = io.WriteString(s, errorMessage(e))
	case 'q':
		_, _ = fmt.Fprintf(s, "%q", errorMessage(e))
	}
}

func (e *appErrorWithCause) Error() string {
	return e.cause.Error()
}

func (e *appErrorWithCause) Format(s fmt.State, verb rune) {
	switch verb {
	case 'v':
		if s.Flag('+') {
			_, _ = fmt.Fprintf(s, "%+v\n", e.cause)
			e.appErrorWithStack.Format(s, verb)
			return
		}
		fallthrough
	case 's':
		_, _ = io.WriteString(s, e.Error())
	case 'q':
		_, _ = fmt.Fprintf(s, "%q", e.Error())
	}
}

func (e *appErrorWithCause) Unwrap() error {
	return e.cause
}

func (s *stack) Format(st fmt.State, verb rune) {
	switch verb {
	case 'v':
		switch {
		case st.Flag('+'):
			for _, pc := range *s {
				f := perr.Frame(pc)
				_, _ = fmt.Fprintf(st, "\n%+v", f)
			}
		}
	}
}

func Is(err error, cm ErrCode) bool {
	var ae AppError
	if errors.As(err, &ae) {
		return ae.Bare().ErrCode() == cm.ErrCode()
	}
	return false
}
