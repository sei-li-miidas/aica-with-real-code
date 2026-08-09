package serializer

import (
	"database/sql/driver"
	"encoding/json"
)

func StdJSONValue[T any](src T) (driver.Value, error) {
	b, err := json.Marshal(&src)
	if err != nil {
		return nil, err
	}
	return bs2s(b), nil
}
