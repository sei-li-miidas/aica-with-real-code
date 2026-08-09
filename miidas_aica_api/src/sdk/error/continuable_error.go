package error

import (
	"errors"
)

// ContinuableErrLogKey 続行許容エラーを表すログカラム名。対となるログカラム値にはIsContinuableErr()の第一戻り値を渡すことを想定
const ContinuableErrLogKey string = "continuable"

// ContinuableErr 続行許容エラーを表す
type ContinuableErr interface {
	error
	Continuable() bool
	Reason() string
	Unwrap() error
}

type continuableErr struct {
	error
	reason string
}

func (e continuableErr) Continuable() bool {
	return true
}

func (e continuableErr) Reason() string {
	return e.reason
}

func (e continuableErr) Unwrap() error {
	return e.error
}

// ToContinuableErr 続行許容エラーとしてマーキングする
// reasonには理由をフリーフォーマットで示すことを想定
func ToContinuableErr(err error, reason string) ContinuableErr {
	e := &continuableErr{
		error:  err,
		reason: reason,
	}
	return e
}

func IsContinuable(err error) (reason string, isContinuable bool) {
	if ce, ok := err.(ContinuableErr); ok {
		return ce.Reason(), ce.Continuable()
	}
	var ce ContinuableErr
	if errors.As(err, &ce) {
		return ce.Reason(), ce.Continuable()
	}
	return "", false
}

func AsContinuable(err error) ContinuableErr {
	if ce, ok := err.(ContinuableErr); ok {
		return ce
	}
	var ce ContinuableErr
	if errors.As(err, &ce) {
		return ce
	}
	return nil
}
