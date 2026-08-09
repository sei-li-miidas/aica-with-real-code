package xsv

import (
	"strconv"
)

// Integer64 64bitの数値
type Integer64 interface {
	int64 | uint64
}

// Formatter Formatter/Parser
type Formatter[V Integer64] interface {
	// Format Inter64を文字列にする
	Format(V) string

	// Parse 文字列をInteger64にする
	Parse(string) (V, error)
}

var (
	Int64Formatter  Formatter[int64]  = int64Formatter{}
	Uint64Formatter Formatter[uint64] = uint64Formatter{}
)

type int64Formatter struct {
}

func (f int64Formatter) Parse(v string) (int64, error) {
	return strconv.ParseInt(v, 10, 64)
}

func (f int64Formatter) Format(v int64) string {
	return strconv.FormatInt(v, 10)
}

type uint64Formatter struct {
}

func (f uint64Formatter) Parse(v string) (uint64, error) {
	return strconv.ParseUint(v, 10, 64)
}

func (f uint64Formatter) Format(v uint64) string {
	return strconv.FormatUint(v, 10)
}
