package error

import (
	"fmt"
)

// Cleanup パニックを処理します。
// goroutineの中での利用を想定しています。
//
// 例
//
//	go func() {
//	   defer Cleanup(func(err error) {
//	       logger.Error("your message", "detail", err)
//	   })
//	   // 様々な処理
//	}()
func Cleanup(handlers ...func(error)) {
	err := PanicToError(recover())
	if err != nil {
		for _, handler := range handlers {
			handler(err)
		}
	}
}

// PanicToError panicをerrorに変換します
func PanicToError(r interface{}) error {
	if r == nil {
		return nil
	}
	switch x := r.(type) {
	case string:
		return fmt.Errorf("recover panic: %s", x)
	case fmt.Stringer:
		return fmt.Errorf("recover panic: %s", x.String())
	case error:
		return x
	default:
		return fmt.Errorf("recover unknown panic: %v", x)
	}
}
