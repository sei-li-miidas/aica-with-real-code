package support

import (
	"math"
)

const (
	HIGH_SALARY_MAX_Y = 200.0 // 最大上げ幅
	HIGH_SALARY_MIN_Y = 0.0   // 最低上げ幅
	HIGH_SALARY_MID_X = 450.0 // X軸の中間値（1000 - 100）/ 2 = 450
	HIGH_SALARY_K     = -0.01 // 角度
)

// 希望年収から高年収テーマの年収の条件を計算する
func CalculateHighSalary(salary int) int {
	floatSalary := float64(salary)

	// 割り算の上の部分
	dividend := HIGH_SALARY_MAX_Y - HIGH_SALARY_MIN_Y

	exponent := -HIGH_SALARY_K * (floatSalary - HIGH_SALARY_MID_X)

	// 割り算の下の部分
	divisor := 1 + math.Exp(exponent)

	// 上げ幅
	high_salary_addition := math.Round((dividend / divisor) + HIGH_SALARY_MIN_Y)
	result := salary + int(high_salary_addition)
	return result
}
