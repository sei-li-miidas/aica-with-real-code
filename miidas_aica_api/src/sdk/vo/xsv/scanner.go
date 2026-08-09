package xsv

import (
	"fmt"
	"strings"

	"golang.org/x/exp/constraints"
)

const (
	TabSeparator   = "\t"
	CommaSeparator = ","
)

// convertToStringSlice valueを文字列化し、sepで分割されたsliceにして返す。
// valueは[]uint8とstringに対応しています。
func convertToStringSlice(value any, sep string) ([]string, error) {
	if value == nil {
		return nil, nil
	}

	switch v := value.(type) {
	case []uint8:
		if len(v) == 0 {
			return []string{}, nil
		}
		return strings.Split(string(v), sep), nil
	case string:
		if len(v) == 0 {
			return []string{}, nil
		}
		return strings.Split(v, sep), nil
	default:
		return nil, fmt.Errorf("unsupported type. type=%T", value)
	}
}

// ScanInteger constraints.Integerの型に変換するScan
func ScanInteger[B Integer64, V constraints.Integer](e Formatter[B], value any, sep string) ([]V, error) {
	cols, err := convertToStringSlice(value, sep)
	if err != nil {
		return nil, err
	}
	if cols == nil {
		return nil, nil
	}

	tmp := make([]V, len(cols))
	for idx, col := range cols {
		i, _ := e.Parse(col)
		tmp[idx] = V(i)
	}
	return tmp, nil
}

// ScanString stringに変換するScan
func ScanString[V ~string](value any, sep string) ([]V, error) {
	cols, err := convertToStringSlice(value, sep)
	if err != nil {
		return nil, err
	}
	if cols == nil {
		return nil, nil
	}

	tmp := make([]V, len(cols))
	for idx, col := range cols {
		tmp[idx] = V(col)
	}
	return tmp, nil
}

// FormatInteger int系の型をcsv/tsvにフォーマットする
func FormatInteger[B Integer64, V constraints.Integer](e Formatter[B], ints []V, sep string) string {
	tmp := make([]string, len(ints))
	for idx, v := range ints {
		tmp[idx] = e.Format(B(v))
	}
	return strings.Join(tmp, sep)
}

// FormatString string系の型をcsv/tsvにフォーマットする
func FormatString[V ~string](strs []V, sep string) string {
	tmp := make([]string, len(strs))
	for idx, v := range strs {
		tmp[idx] = string(v)
	}
	return strings.Join(tmp, sep)
}
