package logger

import (
	"fmt"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/pkgerrors"
)

// print はレベル付きのログ出力
func print(level func() *zerolog.Event, msg string, keyvals ...any) {
	var kvs []any
	kvs = append(kvs, keyvals...)
	if len(keyvals)%2 != 0 {
		kvs = append(keyvals, "ARGUMENTS MUST BE EVEN NUMBERS")
	}

	e := level().Timestamp()
	for i := 0; i < len(kvs); i += 2 {
		key := GenKey(kvs[i])
		v := kvs[i+1]
		e = apply(e, key, v)
	}
	if msg == "" {
		e.Send()
	} else {
		e.Msg(msg)
	}
}

// GenKey はkのstring表現を返す
func GenKey(k any) string {
	switch x := k.(type) {
	case string:
		return x
	case fmt.Stringer:
		return x.String()
	default:
		return fmt.Sprint(x)
	}
}

// apply はログに出力する値の型ごとの処理を適用する
func apply(e *zerolog.Event, key string, v any) *zerolog.Event {
	switch x := v.(type) {
	case int:
		e = e.Int(key, x)
	case int64:
		e = e.Int64(key, x)
	case []int:
		e = e.Ints(key, x)
	case string:
		e = e.Str(key, x)
	case []string:
		e = e.Strs(key, x)
	case []byte:
		e = e.Bytes(key, x)
	case time.Time:
		e = e.Time(key, x)
	case time.Duration:
		e = e.Dur(key, x)
	case float64:
		e = e.Float64(key, x)
	case error:
		e = e.AnErr(key, fmt.Errorf("%+v", x))
		if ret := pkgerrors.MarshalStack(x); ret != nil {
			e = e.Interface("stack", ret)
		}
	default:
		e = e.Interface(key, x)
	}
	return e
}
