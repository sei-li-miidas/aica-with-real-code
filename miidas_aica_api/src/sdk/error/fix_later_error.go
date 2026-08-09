package error

import (
	"errors"
)

// FixLaterLogKey あとで直すエラーを表すログカラム名。対となるログカラム値にはIsFixLater()の第一戻り値を渡すことを想定
const FixLaterLogKey string = "fix-later"

// FixLater あとで直すエラーを表す
type FixLater interface {
	error
	FixLater() bool
	When() string
	Unwrap() error
}

type fixLaterError struct {
	error
	when string
}

func (e fixLaterError) FixLater() bool {
	return true
}

func (e fixLaterError) When() string {
	return e.when
}

func (e fixLaterError) Unwrap() error {
	return e.error
}

// ToFixLater あとで直すエラーとしてマーキングする
// whenにはRedmineチケット番号を「refs #xxxxx」形式で示すことを想定
func ToFixLater(err error, when string) FixLater {
	e := &fixLaterError{
		error: err,
		when:  when,
	}
	return e
}

func IsFixLater(err error) (when string, isFixLater bool) {
	if fl, ok := err.(FixLater); ok {
		return fl.When(), fl.FixLater()
	}
	var fl FixLater
	if errors.As(err, &fl) {
		return fl.When(), fl.FixLater()
	}
	return "", false
}

func AsFixLater(err error) FixLater {
	if fl, ok := err.(FixLater); ok {
		return fl
	}
	var fl FixLater
	if errors.As(err, &fl) {
		return fl
	}
	return nil
}
