package support

import "fmt"

func ConvertDayOffs(dayOffs *[]string) ([]int32, error) {
	if dayOffs == nil || len(*dayOffs) == 0 {
		return nil, nil
	}

	values := make([]int32, 0, len(*dayOffs))
	for _, label := range *dayOffs {
		switch label {
		case "土日祝休み":
			values = append(values, 1)
		case "毎週2日休み":
			values = append(values, 2)
		case "その他":
			values = append(values, 3, 4)
		default:
			return nil, fmt.Errorf("不正な休日種別の値です: %s", label)
		}
	}
	return values, nil
}

func ConvertAverageOvertime(overtime *string) (int32, error) {
	if overtime == nil || *overtime == "" {
		return 0, nil
	}

	switch *overtime {
	case "原則なし":
		return 1, nil
	case "10時間以内":
		return 2, nil
	default:
		return 0, fmt.Errorf("不正な平均残業時間の値です: %s", *overtime)
	}
}
