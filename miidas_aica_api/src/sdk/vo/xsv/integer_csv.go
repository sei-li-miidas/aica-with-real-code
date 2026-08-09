package xsv

import (
	"database/sql/driver"

	"golang.org/x/exp/constraints"
)

// IntCSV サイン付きintegerのCSV
type IntCSV[V constraints.Signed] []V

func (l IntCSV[V]) String() string {
	return FormatInteger[int64, V](Int64Formatter, l, CommaSeparator)
}

func (l *IntCSV[V]) Scan(value any) error {
	tmp, err := ScanInteger[int64, V](Int64Formatter, value, CommaSeparator)
	if err != nil {
		return err
	}
	*l = tmp
	return nil
}

func (l IntCSV[V]) Value() (driver.Value, error) {
	return l.String(), nil
}

// UintCSV サインなしintegerのCSV
type UintCSV[V constraints.Unsigned] []V

func (l UintCSV[V]) String() string {
	return FormatInteger[uint64, V](Uint64Formatter, l, CommaSeparator)
}

func (l *UintCSV[V]) Scan(value any) error {
	tmp, err := ScanInteger[uint64, V](Uint64Formatter, value, CommaSeparator)
	if err != nil {
		return err
	}
	*l = tmp
	return nil
}

func (l UintCSV[V]) Value() (driver.Value, error) {
	return l.String(), nil
}
