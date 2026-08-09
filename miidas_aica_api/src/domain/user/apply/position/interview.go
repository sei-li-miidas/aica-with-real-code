package position

import (
	"database/sql/driver"

	"aica/api/domain/public/master"
	"aica/api/sdk/gormio/serializer"
	"aica/api/sdk/vo/xsv"
)

type (
	// Interview 面接設定
	Interview struct {
		Shared         SharedSetting  // 共通設定
		Meeting        Meeting        // 対面面接設定
		Online         Online         // オンライン面接設定
		Phone          Phone          // 電話面接設定
		WorkExperience WorkExperience // リアル職場体験
	}
	SharedSetting struct {
		EstimatedTerm                string                           // 選考期間
		InterviewTimes               InterviewTimes                   // 面接回数
		SelectionAptitudeTestExists  bool                             // 選考適正試験有無
		SelectionPaperTestExists     bool                             // 選考筆記試験有無
		SelectionPracticalTestExists bool                             // 選考実技試験有無
		SelectionOtherTestExists     bool                             // 選考その他試験有無
		SelectionRemarks             string                           // 選考補足
		CasualDressFlg               bool                             // 面接時私服OKフラグ
		Interviewers                 xsv.IntCSV[master.InterviewerID] // 面接官
		OtherInterviewer             string                           // 面接官（その他）
		Contact                      string                           // 連絡先
	}
	Meeting struct {
		EnableFlg                    bool               // 実施ON/OFF
		PossibleWeekdayHourFrom      int                // 面接可能平日時間From
		PossibleWeekdayHourTo        int                // 面接可能平日時間To
		PossibleWeekendFlg           bool               // 面接可能土日祝日フラグ
		PossibleTimeComplement       string             // 面接可能日時補足
		Minutes                      int                // 面接所要時間（分）
		PlaceOptions                 xsv.StrTSV[string] // 面接場所候補TSV(対面のみ)
		TransportationPaymentFlg     bool               // 交通費支給フラグ（対面のみ）
		TransportationPaymentRemarks string             // 交通費支給（備考）
	}
	Online struct {
		EnableFlg               bool   // 実施ON/OFF
		PossibleWeekdayHourFrom int    // 面接可能平日時間From
		PossibleWeekdayHourTo   int    // 面接可能平日時間To
		PossibleWeekendFlg      bool   // 面接可能土日祝日フラグ
		PossibleTimeComplement  string // 面接可能日時補足
		Minutes                 int    // 面接所要時間（分）
	}
	Phone struct {
		EnableFlg               bool   // 実施ON/OFF
		PossibleWeekdayHourFrom int    // 面接可能平日時間From
		PossibleWeekdayHourTo   int    // 面接可能平日時間To
		PossibleWeekendFlg      bool   // 面接可能土日祝日フラグ
		PossibleTimeComplement  string // 面接可能日時補足
		Minutes                 int    // 面接所要時間（分）
	}
	// リアル職場体験
	WorkExperience struct {
		PatternID        master.WorkExperiencePatternID                 // 実施方式
		TimingID         master.WorkExperienceTimingID                  // 実施タイミング
		TimingRemarks    string                                         // 実施タイミング補足
		OtherTimingText  string                                         // その他の実施タイミングの備考
		WorkTypeIDs      xsv.IntTSV[master.WorkExperienceContentTypeID] // 実施内容
		WorkContent      string                                         // 実施内容詳細
		TimeframeID      master.WorkExperienceTimeframeID               // 実施日時
		TimeframeRemarks string                                         // 実施日時補足
		NeedTimeID       master.WorkExperienceNeedtimeID                // 所要時間
		NeedTimeRemarks  string                                         // 所要時間補足
		RewardID         master.WorkExperienceRewardID                  // 報酬設定
		RewardValue      int                                            // 報酬額
		RewardRemarks    string                                         // 報酬補足
	}
)

// HasEnabledMethod 有効化された面接方法があるか
func (i *Interview) HasEnabledMethod() bool {
	return i.Meeting.EnableFlg || i.Online.EnableFlg || i.Phone.EnableFlg
}

func (i *Interview) Scan(value interface{}) error {
	return serializer.JsoniterJSONScan(i, value)
}

func (i Interview) Value() (driver.Value, error) {
	return serializer.StdJSONValue(i)
}

// HasMultipleOptions 選考方法に選択肢（入力項目を含む）があるか
func (i *Interview) HasMultipleOptions() bool {
	if (i.Meeting.EnableFlg && len(i.Meeting.PlaceOptions) >= 2) || i.Phone.EnableFlg || i.WorkExperience.PatternID.IsApplicantsOnly() {
		return true
	}
	return i.Meeting.EnableFlg && i.Online.EnableFlg
}
