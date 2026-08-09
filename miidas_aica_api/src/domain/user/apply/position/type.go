package position

type AutoOfferStatus int

const (
	AutoOfferStatusNotSet  AutoOfferStatus = 0 // 未設定
	_                      AutoOfferStatus = 1 // 一時保存中はなくなりました。
	AutoOfferStatusSending AutoOfferStatus = 2 // 自動オファー送信中
	AutoOfferStatusManual  AutoOfferStatus = 3 // 手動オファー送信中
	AutoOfferStatusStopped AutoOfferStatus = 4 // 面接確約停止中
)

type BackwardCompatibleType int

const (
	BackwardCompatibleTypeNormal  BackwardCompatibleType = 0 // 通常
	_                             BackwardCompatibleType = 1 // 後方互換データ（欠番）
	BackwardCompatibleTypeInvalid BackwardCompatibleType = 2 // 非互換データ (機能移行後も勝手には削除できずやむなく残っているデータ)
)

// IsAutoOfferSending 自動オファーを送信しているか？
func (s AutoOfferStatus) IsAutoOfferSending() bool {
	return s == AutoOfferStatusSending
}

// IsManualOfferSending 手動面接確約オファーを送信しているか？
func (s AutoOfferStatus) IsManualOfferSending() bool {
	return s == AutoOfferStatusManual
}

type InterviewTimes int // 面接回数

const (
	NotDescribe     InterviewTimes = 0
	Once            InterviewTimes = 1
	Twice           InterviewTimes = 2
	ThreeTimes      InterviewTimes = 3
	FourTimesOrMore InterviewTimes = 4
)

func (interviewTimes InterviewTimes) Convert2String() string {
	switch interviewTimes {
	case NotDescribe:
		return ""
	case Once:
		return "1回"
	case Twice:
		return "2回"
	case ThreeTimes:
		return "3回"
	case FourTimesOrMore:
		return "4回以上"
	}
	return ""
}

type (
	// CompetencyMatchRank コンピテンシーマッチ度合い。
	// 市場価値診断サーバーで算出した値。 [pkg/miidas/m2/domain/matching/model.CompetencyMatchRank]
	CompetencyMatchRank int

	// TargetMatchRank 募集条件一致率（ターゲットマッチ度合い）
	// 市場価値診断サーバーで算出した値。 [pkg/miidas/m2/domain/matching/model.TargetMatchRank]
	TargetMatchRank int
)
