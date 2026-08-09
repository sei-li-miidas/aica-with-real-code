package serializer

import (
	"fmt"

	jsoniter "github.com/json-iterator/go"
)

func JsoniterJSONScan[T any](dst *T, value any) error {
	var bytes []byte
	switch v := value.(type) {
	case []byte:
		bytes = v
	case string:
		bytes = s2bs(v)

	default:
		return fmt.Errorf("unsupported type. type: %T", value)
	}

	if len(bytes) == 0 {
		return nil
	}
	if err := jsoniter.ConfigCompatibleWithStandardLibrary.Unmarshal(bytes, dst); err != nil {
		return err
	}
	return nil
}
