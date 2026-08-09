package master

import (
	"github.com/samber/lo"

	"aica/api/sdk/slice"
)

type (
	TraitPositionOption struct {
		TraitPositionID MasterTraitPositionID
		Value           int
		Name            string
		UserSideName    string
		SortOrder       int
	}

	// TraitPositionOptionForUser ユーザー向け
	TraitPositionOptionForUser struct {
		TraitPositionID MasterTraitPositionID
		Value           int
		UserSideName    string
		SortOrder       int
	}

	// TraitPositionOptionForCorp 企業向け
	TraitPositionOptionForCorp struct {
		TraitPositionID MasterTraitPositionID
		Value           int
		CorpSideName    string
		SortOrder       int
	}

	TraitPositionOptionListForUser []*TraitPositionOptionForUser
	TraitPositionOptionListForCorp []*TraitPositionOptionForCorp
)

func (TraitPositionOption) TableName() string {
	return "master.trait_position_option"
}

func (m *TraitPositionOptionForUser) GetUserSideName() string {
	if m == nil {
		return ""
	}
	return m.UserSideName
}

func (s TraitPositionOptionListForUser) ValueMap() map[int]*TraitPositionOptionForUser {
	return lo.SliceToMap(s, func(e *TraitPositionOptionForUser) (int, *TraitPositionOptionForUser) {
		return e.Value, e
	})
}

func (s TraitPositionOptionListForUser) Get(value int) *TraitPositionOptionForUser {
	if row, found := slice.Find(s, func(e *TraitPositionOptionForUser) bool {
		return e.Value == value
	}); found {
		return row
	} else {
		return nil
	}
}

func (s TraitPositionOptionListForCorp) ValueMap() map[int]*TraitPositionOptionForCorp {
	return lo.SliceToMap(s, func(e *TraitPositionOptionForCorp) (int, *TraitPositionOptionForCorp) {
		return e.Value, e
	})
}

const (
	BonusCountNone  = 1 // 待遇_賞与 なし
	BonusCount1     = 2 // 待遇_賞与 年1回
	BonusCount2     = 3 // 待遇_賞与 年2回
	BonusCount3     = 4 // 待遇_賞与 年3回
	BonusCount4Over = 5 // 待遇_賞与 年4回以上

	PromotionCountNone  = 1 // 待遇_昇給・昇格 なし
	PromotionCount1     = 2 // 待遇_昇給・昇格 年1回
	PromotionCount2     = 3 // 待遇_昇給・昇格 年2回
	PromotionCount3     = 4 // 待遇_昇給・昇格 年3回
	PromotionCount4Over = 5 // 待遇_昇給・昇格 年4回以上

	RemoteWorkNg              = 1 // リモート勤務 NG
	RemoteWorkOkConditionally = 2 // リモート勤務 OK（条件あり）
	RemoteWorkOkFully         = 3 // リモート勤務 OK（条件なし）

	HolidayRestAtWeekendPublicHoliday = 1 // 休日 土日祝休み
	HolidayTwoDayHolidayEveryWeek     = 2 // 休日 完全週休2日制
	HolidayTwoDayHolidayNotEveryWeek  = 3 // 休日 週休2日制
	HolidayOther                      = 4 // 休日 その他

	OvertimeAvgOverTimeWorkNone   = 1 // 労働環境_平均残業時間 原則なし
	OvertimeAvgOverTimeWork10     = 2 // 労働環境_平均残業時間 10時間以内
	OvertimeAvgOverTimeWork20     = 3 // 労働環境_平均残業時間 20時間以内
	OvertimeAvgOverTimeWork30     = 4 // 労働環境_平均残業時間 30時間以内
	OvertimeAvgOverTimeWork40     = 5 // 労働環境_平均残業時間 40時間以内
	OvertimeAvgOverTimeWork40Over = 6 // 労働環境_平均残業時間 40時間以上

	ModelAnnualIncomeTwenties = "20代" // Deprecated: NW トレイトの値を直接参照しない 意思決定と裁量のグループ名
	ModelAnnualIncomeThirties = "30代" // Deprecated: NW トレイトの値を直接参照しない 意思決定と裁量のグループ名
	ModelAnnualIncomeForties  = "40代" // Deprecated: NW トレイトの値を直接参照しない 意思決定と裁量のグループ名

	TransferenceNotExists = 1 // 国内転勤 国内転勤なし

	TransferenceAbroadExists            = 1 // 海外転勤 海外転勤あり
	TransferenceAbroadNotExists         = 2 // 海外転勤 海外転勤なし（予定もなし）
	TransferenceAbroadNotExistsHavePlan = 3 // 海外転勤 海外転勤なし（予定あり）

	TransferenceAbroadUseEnglish    = 1 // 英語力 英語力必須
	TransferenceAbroadNotUseEnglish = 2 // 英語力 英語力不問

	HREvaluationTypeGroup1 = "（1）" // NW トレイトの値を直接参照しない 評価基準の特徴のグループ名 実力主義〜
	HREvaluationTypeGroup2 = "（2）" // NW トレイトの値を直接参照しない 評価基準の特徴のグループ名 長所を伸ばす〜
	HREvaluationTypeGroup3 = "（3）" // NW トレイトの値を直接参照しない 評価基準の特徴のグループ名 成果を重視〜
	HREvaluationTypeGroup4 = "（4）" // NW トレイトの値を直接参照しない 評価基準の特徴のグループ名 個性重視〜

	PtjAccomplishmentRateLess50 = 1 // 業績目標達成者率 50%未満
	PtjAccomplishmentRateOver50 = 2 // 業績目標達成者率 50%以上
	PtjAccomplishmentRateOver60 = 3 // 業績目標達成者率 50%以上
	PtjAccomplishmentRateOver70 = 4 // 業績目標達成者率 50%以上
	PtjAccomplishmentRateOver80 = 5 // 業績目標達成者率 50%以上
	PtjAccomplishmentRateOver90 = 6 // 業績目標達成者率 50%以上
	PtjAccomplishmentRateNoRate = 7 // 業績目標達成者率 個人目標がない

	ContractExtensionOk = 1 // 契約延長あり

	WorkingEnvironmentClothes         = 5  // 私服勤務
	WorkingEnvironmentByCar           = 6  // マイカー通勤
	WorkingEnvironmentWalk5Min        = 8  // 徒歩5分以内
	WorkingEnvironmentWalk10Min       = 9  // 徒歩10分以内
	WorkingEnvironmentNotRained       = 10 // 駅から雨に濡れない
	WorkingEnvironmentEnglish         = 11 // 社内公用語が英語
	WorkingEnvironmentTimeArrangeable = 13 // 出勤時間・退社時間は自由に決められる

	WorkTimeFixed = 1 // 勤務時間 固定制
	WorkTimeShift = 2 // 勤務時間 シフト制
)

// PositionEmploymentTypeID ポジションの契約形態
type PositionEmploymentTypeID int

const (
	PositionEmploymentTypeIDEmployee              PositionEmploymentTypeID = 1 // 正社員
	PositionEmploymentTypeIDContract              PositionEmploymentTypeID = 2 // 契約社員
	_                                             PositionEmploymentTypeID = 3 // 役員（任用契約）
	PositionEmploymentTypeIDOutsourcing           PositionEmploymentTypeID = 4 // 業務委託（レギュラー）
	PositionEmploymentTypeIDSpotOutsourcing       PositionEmploymentTypeID = 5 // 業務委託（スポット）
	PositionEmploymentTypeIDCommissionOutsourcing PositionEmploymentTypeID = 6 // 業務委託（完全歩合制）
)

// IsContract 契約社員か
func (p PositionEmploymentTypeID) IsContract() bool {
	return p == PositionEmploymentTypeIDContract
}

// IsJobChange 転職の契約形態か
func (p PositionEmploymentTypeID) IsJobChange() bool {
	switch p {
	case PositionEmploymentTypeIDEmployee, PositionEmploymentTypeIDContract:
		return true
	default:
		return false
	}
}

// IsRegular レギュラー業務委託か
func (p PositionEmploymentTypeID) IsRegular() bool {
	return p == PositionEmploymentTypeIDOutsourcing
}

// IsSpot スポット業務委託か
func (p PositionEmploymentTypeID) IsSpot() bool {
	return p == PositionEmploymentTypeIDSpotOutsourcing
}

// IsCommission 完全歩合制業務委託か
func (p PositionEmploymentTypeID) IsCommission() bool {
	return p == PositionEmploymentTypeIDCommissionOutsourcing
}

// IsOutsourcing 業務委託か
func (p PositionEmploymentTypeID) IsOutsourcing() bool {
	return p.IsRegular() || p.IsSpot() || p.IsCommission()
}
