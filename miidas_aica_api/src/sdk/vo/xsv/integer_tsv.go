package xsv

import (
	"database/sql/driver"
	"slices"

	"golang.org/x/exp/constraints"
)

// IntTSV サイン付きintegerのTSV
type IntTSV[V constraints.Signed] []V

func (l IntTSV[V]) String() string {
	return FormatInteger[int64, V](Int64Formatter, l, TabSeparator)
}

func (l *IntTSV[V]) Scan(value any) error {
	tmp, err := ScanInteger[int64, V](Int64Formatter, value, TabSeparator)
	if err != nil {
		return err
	}
	*l = tmp
	return nil
}

func (l IntTSV[V]) Value() (driver.Value, error) {
	return l.String(), nil
}

func (l IntTSV[V]) Contains(v V) bool {
	return slices.Contains(l, v)
}

func (l IntTSV[V]) Values() []V {
	return l
}

// UintTSV サインなしintegerのTSV
type UintTSV[V constraints.Unsigned] []V

func (l UintTSV[V]) String() string {
	return FormatInteger[uint64, V](Uint64Formatter, l, TabSeparator)
}

func (l *UintTSV[V]) Scan(value any) error {
	tmp, err := ScanInteger[uint64, V](Uint64Formatter, value, TabSeparator)
	if err != nil {
		return err
	}
	*l = tmp
	return nil
}

func (l UintTSV[V]) Value() (driver.Value, error) {
	return l.String(), nil
}

func (l UintTSV[V]) Contains(v V) bool {
	return slices.Contains(l, v)
}

func (l UintTSV[V]) Values() []V {
	return l
}
