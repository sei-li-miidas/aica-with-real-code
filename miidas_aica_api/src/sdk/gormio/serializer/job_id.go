package serializer

import (
	"bytes"
	"database/sql/driver"
	"encoding/json"
	"fmt"
	"strconv"

	"golang.org/x/exp/constraints"
)

var jsonNullLiteral = []byte("null")

func JobIDScan[T constraints.Integer](dst *T, value any) error {
	var id int

	switch v := value.(type) {
	case int:
		id = v

	case int8:
		id = int(v)
	case int16:
		id = int(v)
	case int32:
		id = int(v)
	case int64:
		id = int(v)

	case []byte:
		var err error
		id, err = strconv.Atoi(bs2s(v))
		if err != nil {
			return err
		}
	case string:
		var err error
		id, err = strconv.Atoi(v)
		if err != nil {
			return err
		}
	default:
		return fmt.Errorf("JobIDScan: unsupported type. type: %T", value)
	}

	*dst = T(id)
	return nil
}

// JobIDValue 互換性維持のため文字列に変換
func JobIDValue[T constraints.Integer](src T) (driver.Value, error) {
	return strconv.Itoa(int(src)), nil
}

// JobIDUnmarshalJSON 数値・文字列両方に対応するため、 json.Number を使う
func JobIDUnmarshalJSON[T constraints.Integer](dst *T, value []byte) error {
	if bytes.Equal(value, jsonNullLiteral) {
		return nil
	}

	var number json.Number
	if err := json.Unmarshal(value, &number); err != nil {
		return err
	}

	i, err := number.Int64()
	if err != nil {
		return err
	}

	*dst = T(i)
	return nil
}

// JobIDMarshalJSON 互換性維持のため文字列に変換
func JobIDMarshalJSON[T constraints.Integer](value T) ([]byte, error) {
	return s2bs(strconv.Itoa(int(value))), nil
	// strid := strconv.Itoa(int(value))
	// return json.Marshal(strid)
}
