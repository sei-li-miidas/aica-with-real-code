/*
環境変数を取得するためのユーティリティパッケージです。

MIIDAS用の環境変数は一定のルールで命名されていて、それを簡単に扱えるようにPrefixerと定数を用意しています。
*/
package env

import (
	"os"
	"strconv"
	"strings"

	"github.com/pkg/errors"
	"github.com/samber/lo"
)

var (
	ErrCantGet     = errors.New("can't get environment variable")
	ErrCantConvert = errors.New("can't convert")
)

const (
	// separator 環境変数の名前の区切り文字
	separator = "_"
)

// Key は与えられたパーツを結合し環境変数名を返します。
// 前後のセパレーターは上手く処理します。
//
// あちこちで使うものでもないと思うので、以下には対応してません。
// 1. 途中にあるセパレーターはそのままです。
// 2. 前後、途中にあるスペースはそのままです。
// 3. 先頭、末尾にセパレーターがある環境変数は扱えません。
// 4. 連続したセパレーターは対応してません。
func Key(keys ...string) string {
	if len(keys) == 0 {
		return ""
	}

	var trimedKeys []string
	for _, k := range keys {
		trimedKeys = append(trimedKeys, strings.Trim(k, separator))
	}
	return strings.Join(trimedKeys, separator)
}

// Exists は環境変数の有無を返します。
func Exists(keys ...string) bool {
	return exists(keys...)()
}

// Get は環境変数を取得します。
func Get(keys ...string) (string, error) {
	return get(keys...)()
}

// MustGet は環境変数を取得します。
func MustGet(keys ...string) string {
	return lo.Must(Get(keys...))
}

// GetInt はintの環境変数を取得します。
func GetInt(keys ...string) (int, error) {
	return getInt(keys...)()
}

// MustGetInt は環境変数を取得します。
func MustGetInt(keys ...string) int {
	return lo.Must(GetInt(keys...))
}

// GetStrCSV は要素が文字列のcsvを取得します。
// 各要素の前後のスペースっぽい文字をtrimしています。
func GetStrCSV(keys ...string) ([]string, error) {
	return getStrCSV(keys...)()
}

func key(prefixes ...string) func(...string) string {
	return func(keys ...string) string {
		return Key(append(prefixes, keys...)...)
	}
}

func exists(prefixes ...string) func(...string) bool {
	return func(keys ...string) bool {
		fullKey := key(prefixes...)(keys...)
		_, found := os.LookupEnv(fullKey)
		return found
	}
}

func get(prefixes ...string) func(...string) (string, error) {
	return func(keys ...string) (string, error) {
		fullKey := key(prefixes...)(keys...)
		ret, found := os.LookupEnv(fullKey)
		if !found {
			return ret, errors.WithMessagef(ErrCantGet, "missing key: %s", fullKey)
		}
		return ret, nil
	}
}

func mustGet(prefixes ...string) func(...string) string {
	return func(keys ...string) string {
		return lo.Must(get(prefixes...)(keys...))
	}
}

func getInt(prefixes ...string) func(...string) (int, error) {
	return func(keys ...string) (int, error) {
		if s, err := get(prefixes...)(keys...); err != nil {
			return 0, err
		} else if i, err := strconv.Atoi(s); err != nil {
			return 0, err
		} else {
			return i, nil
		}
	}
}

func mustGetInt(prefixes ...string) func(...string) int {
	return func(keys ...string) int {
		return lo.Must(getInt(prefixes...)(keys...))
	}
}

func getStrCSV(prefixes ...string) func(...string) ([]string, error) {
	return func(keys ...string) ([]string, error) {
		if s, err := get(prefixes...)(keys...); err != nil {
			return nil, err
		} else {
			rawCSV := strings.Split(s, ",")

			var csv []string
			for _, rawE := range rawCSV {
				e := strings.TrimSpace(rawE)
				if len(e) == 0 {
					continue
				}
				csv = append(csv, e)
			}
			return csv, nil
		}
	}
}

func getBool(prefixes ...string) func(...string) (bool, error) {
	return func(keys ...string) (bool, error) {
		if s, err := get(prefixes...)(keys...); err != nil {
			return false, err
		} else if parse, err := strconv.ParseBool(s); err != nil {
			return parse, err
		} else {
			return parse, nil
		}
	}
}
