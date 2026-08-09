package xsv

import (
	"database/sql/driver"
)

// StrTSV 文字列のTSV
// クォーティングとかはしてないので、要素にタブが入らないものに使うこと
type StrTSV[V ~string] []V

func (l StrTSV[V]) String() string {
	return FormatString(l, TabSeparator)
}

func (l *StrTSV[V]) Scan(value any) error {
	tmp, err := ScanString[V](value, TabSeparator)
	if err != nil {
		return err
	}
	*l = tmp
	return nil
}

func (l StrTSV[V]) Value() (driver.Value, error) {
	return l.String(), nil
}
