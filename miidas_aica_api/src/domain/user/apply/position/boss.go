package position

import (
	"aica/api/sdk/vo/exam/competency"
	"database/sql/driver"
	"encoding/json"
	"fmt"
)

type (
	BossList []Boss // ポジションに登録されている上司情報一覧

	// Boss コンピテンシー診断結果「上下関係適性」の上司タイプ
	Boss struct {
		Directive   competency.ScoreValue // 指示型
		Delegation  competency.ScoreValue // 委任型
		Listening   competency.ScoreValue // 傾聴型
		Dialogue    competency.ScoreValue // 対話型
		Negotiation competency.ScoreValue // 交渉型
	}
)

/*
	func (bl *BossList) Scan(value any) error {
		return serializer.JsoniterJSONScan(bl, value)
	}

	func (bl BossList) Value() (driver.Value, error) {
		return serializer.StdJSONValue(bl)
	}
*/
func (bl *BossList) Scan(value interface{}) error {
	switch v := value.(type) {
	case []uint8:
		if len(v) == 0 {
			*bl = nil
			return nil
		}
		var tmp BossList
		if err := json.Unmarshal(value.([]byte), &tmp); err != nil {
			return err
		} else {
			*bl = tmp
			return nil
		}
	default:
		return fmt.Errorf("unsupported type. type:%T", value)
	}
}

func (bl BossList) Value() (driver.Value, error) {
	b, err := json.Marshal(&bl)
	if err != nil {
		return nil, err
	}
	return string(b), nil
}
