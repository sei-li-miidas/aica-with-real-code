package model

import (
	mposition "aica/api/domain/user/apply/position"
	"fmt"
)

type PositionSummary struct {
	ID          mposition.ID
	Title       string
	MainJobText string
	SalaryFrom  *int
	SalaryTo    *int
	Image       string
}

type PositionRecommendation struct {
	Theme       string
	Title       string
	Description string
}

func PositionRecommendations(prefix string) []*PositionRecommendation {
	return []*PositionRecommendation{
		{Theme: fmt.Sprintf("%stheme1", prefix), Title: "ワンランク上の収入を目指す求人", Description: "収入を増やしたい、高い年収の求人で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme2", prefix), Title: "プライベート充実！残業少なめ求人", Description: "プライベート充実！残業少なめ求人で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme3", prefix), Title: "思いを共有して働く企業", Description: "思いを共有して働く企業で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme4", prefix), Title: "長く安心して働ける企業", Description: "長く安心して働ける企業で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme5", prefix), Title: "育児休暇や在宅勤務ができる求人", Description: "育児休暇や在宅勤務ができる求人で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme6", prefix), Title: "産休や女性休暇がとれる企業", Description: "産休や女性休暇がとれる求人で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme7", prefix), Title: "働きやすい企業", Description: "働きやすい企業で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme8", prefix), Title: "女性比率が30%以上の企業", Description: "女性比率が30%以上の企業で新しい可能性を探してみませんか？"},
		{Theme: fmt.Sprintf("%stheme9", prefix), Title: "フレックスタイムや時短勤務ができる求人", Description: "フレックスタイムや時短勤務ができる求人で新しい可能性を探してみませんか？"},
	}
}
