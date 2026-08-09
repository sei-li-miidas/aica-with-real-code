package position

import (
	"database/sql/driver"
	"time"

	mapset "github.com/deckarep/golang-set/v2"
	"github.com/pkg/errors"
	"github.com/samber/lo"

	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/business"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/vo"
	ms3 "aica/api/sdk/aws/s3"
	"aica/api/sdk/gormio/serializer"
	miidasMapset "aica/api/sdk/mapset"
	vo2 "aica/api/sdk/vo"
	"aica/api/sdk/vo/exam/competency"
)

const (
	NewPositionDay = 14 // 新着ポジションの日数(X日以内に初回公開)
)

type (
	// ID ポジションID
	ID int

	// Position ポジション
	Position struct {
		ID                     ID                     `gorm:"primaryKey;autoIncrement:false"` // ポジションID
		CompanyID              company.ID             // 企業ID
		CompanySectionID       company.SectionID      // 企業部門ID
		FirstPublishedAt       *time.Time             `gorm:"column:first_published_at"` // 初回公開日時
		LastNotifiedAt         *time.Time             `gorm:"column:last_notified_at"`   // ユーザーへの最終通知日時
		PublishedAt            *time.Time             `gorm:"column:published_at"`       // 公開日時
		DetailShowableFlg      bool                   // 詳細表示可能フラグ
		TrashedAt              *time.Time             // ゴミ箱設定日時
		LastModifiedAt         time.Time              // 最終更新日時
		AutoOfferStatus        AutoOfferStatus        // 面接確約ユーザー設定 0=未設定 1=一時保存中(廃止済) 2=自動オファー送信中 3=手動オファー送信中 4=面接確約停止中
		BackwardCompatibleType BackwardCompatibleType // データの後方互換タイプ(0:通常、1:後方互換データ、2:非互換データ)
		Detail
		Interview
		BossList   *BossList // 上司の上下関係適性のコンピテンシー結果
		ImportedAt time.Time // インポート日時
	}

	Detail struct {
		Title                             string                  // ポジション名（公開用）
		Post                              *vo.ValueText           `json:",omitempty"` // 役職
		EmploymentType                    *vo.ValueText           `json:",omitempty"` // 契約形態種別
		Images                            Images                  `json:",omitempty"` // 掲載画像
		Jobs                              Jobs                    `json:",omitempty"` // 仕事内容
		MainJobText                       string                  `json:",omitempty"` // 仕事内容(メイン)
		GuaranteedIncome                  *GuaranteedIncome       `json:",omitempty"` // 待遇_確約年収_
		ModelAnnualIncome                 *ModelAnnualIncome      `json:",omitempty"` // 待遇_モデル年収（目安）
		StockOption                       *vo.ValueText           `json:",omitempty"` // 待遇_ストックオプション
		BonusCount                        *vo.ValueText           `json:",omitempty"` // 待遇_賞与
		PromotionCount                    *vo.ValueText           `json:",omitempty"` // 待遇_昇給・昇格
		WorkAddress                       *WorkAddresses          `json:",omitempty"` // 勤務地_都道府県
		RemoteWork                        *RemoteWork             `json:",omitempty"` // リモート勤務
		RemoteWorkCondition               string                  `json:",omitempty"`
		RemoteWorkOfficeFrequency         *vo.ValueText           `json:",omitempty"` // リモート勤務_出社頻度
		Holiday                           *vo.ValueText           `json:",omitempty"` // 休日
		WorkTime                          string                  `json:",omitempty"` // 勤務時間
		WorkTimeSystem                    *vo.ValueText           `json:",omitempty"` // 勤務時間_勤務体制
		WorkTimeNightsShift               *vo.ValueText           `json:",omitempty"` // 勤務時間_夜勤の有無
		OvertimeAvg                       *vo.ValueText           `json:",omitempty"` // 労働環境_平均残業時間
		OfficialTripFrequency             *vo.ValueText           `json:",omitempty"` // 労働環境_出張頻度
		WorkingEnvironment                vo.ValueTexts           `json:",omitempty"` // 労働環境_労働環境の特徴
		TransferenceExists                *vo.ValueText           `json:",omitempty"` // キャリア_国内転勤の有無
		TransferenceFrequency             *vo.ValueText           `json:",omitempty"` // キャリア_国内転勤の有無_国内転勤の頻度
		TransferenceAbroadExists          *vo.ValueText           `json:",omitempty"` // キャリア_海外転勤
		TransferenceAbroadEnglishIsUnused *vo.ValueText           `json:",omitempty"` // キャリア_海外転勤_英語力不問
		BusinessID                        business.ID             `json:",omitempty"` // 事業
		BusinessName                      string                  `json:",omitempty"` // 事業名
		HREvaluationType                  *HREvaluationType       `json:",omitempty"` // 人事評価_評価基準の特徴
		HREvaluationCompetency            *HREvaluationCompetency `json:",omitempty"` // 人事評価_特に評価されるコンピテンシー
		PR                                string                  `json:",omitempty"` // その他_ポジションPR
		SmokeFree                         *vo.ValueText           `json:",omitempty"` // 受動喫煙対策
		SmokeFreeEnvironment              *vo.ValueText           `json:",omitempty"` // 受動喫煙対策（具体的な対策）
		AccomplishmentImportance          *vo.ValueText           `json:",omitempty"` // ポジション特徴_業績目標達成思考
		AccomplishmentRate                *vo.ValueText           `json:",omitempty"` // ポジション特徴_業績目標達成者率
		SalesStyleDive                    *vo.ValueText           `json:",omitempty"` // ポジション特徴_営業スタイル_新規飛び込み
		SalesStyleTelAppointment          *vo.ValueText           `json:",omitempty"` // ポジション特徴_営業スタイル_新規テレアポ
		SalesStyleHost                    *vo.ValueText           `json:",omitempty"` // ポジション特徴_営業スタイル_接待
		BaseMonthlySalary                 *vo.ValueText           `json:",omitempty"` // ポジション特徴_基本月給
		OvertimeSalary                    *OvertimeSalary         `json:",omitempty"` // ポジション特徴_基本月給_固定残業代
		CareerPathOutOfSiteExists         *vo.ValueText           `json:",omitempty"` // ポジション特徴_キャリアパス_1
		CareerPathWorkHeadOfficeExists    *vo.ValueText           `json:",omitempty"` // ポジション特徴_キャリアパス_2
		OrgTrendEngineerManagerExists     *vo.ValueText           `json:",omitempty"` // ポジション特徴_組織_1
		OrgTrendSectionMemberQty          *vo.ValueText           `json:",omitempty"` // ポジション特徴_組織_2
		OrgTrendAccountingLicenceExists   *vo.ValueText           `json:",omitempty"` // ポジション特徴_組織_3
		OrgTrendLegalLicenceExists        *vo.ValueText           `json:",omitempty"` // ポジション特徴_組織_4
		OrgTrendRelatedWithEngineer       *vo.ValueText           `json:",omitempty"` // ポジション特徴_組織_5
		WorkEnvironment                   *vo.ValuesText          `json:",omitempty"` // ポジション特徴_労働環境
		DevelopmentTerm                   *vo.ValueText           `json:",omitempty"` // ポジション特徴_開発スパン
		DevelopmentProcess                *vo.ValueText           `json:",omitempty"` // ポジション特徴_開発手法
		EmergencySupport                  *vo.ValueText           `json:",omitempty"` // ポジション特徴_緊急対応
		JoinedReserve                     int                     `json:",omitempty"` // 待遇_入社支度金
		EmploymentToRegularEmployee       *vo.ValueText           `json:",omitempty"` // 契約形態_契約社員
		Probation                         *vo.ValueText           `json:",omitempty"` // ポジション特徴_試用期間
		ContractPeriod                    *vo.ValueText           `json:",omitempty"` // ポジション特徴_契約期間
		ContractExtension                 *vo.ValueText           `json:",omitempty"` // ポジション特徴_契約延長
		ContractRenewal                   *vo.ValueText           `json:",omitempty"` // ポジション特徴_契約更新
		ContractRenewalText               string                  `json:",omitempty"` // ポジション特徴_契約更新の詳細
		RegularOutsourcing                *RegularOutsourcing     `json:",omitempty"` // 業務委託（レギュラー）
		SpotOutsourcing                   *SpotOutsourcing        `json:",omitempty"` // 業務委託（スポット）
		SpotJobRequest                    *vo.ValueText           `json:",omitempty"` // 業務委託（スポット）依頼内容
		SpotJobDescription                string                  `json:",omitempty"` // 業務委託（スポット）依頼内容（詳細）
		CommissionBusinessDescription     string                  `json:",omitempty"` // 業務委託（完全歩合制）業務内容
		CommissionFeeCondition            string                  `json:",omitempty"` // 業務委託（完全歩合制）報酬
		EmploymentTypeChange              *vo.ValueText           `json:",omitempty"` // 契約形態変更可否
		OutsourcingAppeal                 *OutsourcingAppeal      `json:",omitempty"` // 業務委託ポジションの訴求ポイント
	}
	PublishStatus int
	// RemoteWork リモートワーク
	RemoteWork struct {
		ID    int
		Label string `json:",omitempty"`
		Text  string `json:",omitempty"`
	}
	// Job 職種
	Job struct {
		SmallID     master.JobTypeSmallID // 職種小分類ID
		Label       string                `json:",omitempty"`
		Main        bool                  // メインフラグ
		HasSkills   bool                  // 体系立てたスキルが存在する職種かどうか
		SkillGroups []SkillGroup          // 入力されたスキル（マスタに存在しないスキルの場合もダミーのグループを作って保持）
	}
	Jobs []Job
	// SkillGroup スキルグループ
	SkillGroup struct {
		ID     int
		Skills []Skill
	}
	// Skill スキル
	Skill struct {
		ID     int
		IsMain bool
	}
	// WorkAddresses 勤務地一覧
	WorkAddresses struct {
		Values WorkAddressList
		Text   string `json:",omitempty"` // 勤務地全体に対する補足
	}
	// WorkAddress 勤務地
	WorkAddress struct {
		ID    master.WorkAddressID // 勤務地ID
		Label string               `json:",omitempty"`
		Text  string               `json:",omitempty"` // 勤務地の補足
	}
	WorkAddressList []WorkAddress

	// GuaranteedIncome 確約年収
	GuaranteedIncome struct {
		IncomeFromType      vo2.IncomeFromTypeID
		BulkIncomeFrom      *int   `json:",omitempty"`
		BulkIncomeTo        *int   `json:",omitempty"`
		Text                string `json:",omitempty"`
		OldSalaryYearlyText string `json:",omitempty"`
		Incomes             []vo2.Income
	}

	// ModelAnnualIncome モデル年収(目安)
	ModelAnnualIncome struct {
		Income20s int    `json:",omitempty"`
		Income30s int    `json:",omitempty"`
		Income40s int    `json:",omitempty"`
		Text      string `json:",omitempty"`
	}
	// HREvaluationType 評価基準の特徴
	HREvaluationType struct {
		Type1 int    `json:",omitempty"`
		Type2 int    `json:",omitempty"`
		Type3 int    `json:",omitempty"`
		Type4 int    `json:",omitempty"`
		Text  string `json:",omitempty"`
	}
	// OvertimeSalary 固定残業代
	OvertimeSalary struct {
		HasOvertimeSalary int `json:",omitempty"`
		MonthlyAmount     int `json:",omitempty"`
		ExpectedHours     int `json:",omitempty"`
	}
	// HREvaluationCompetency 特に評価されるコンピテンシー
	HREvaluationCompetency struct {
		Axes []AxisData
		Text string `json:",omitempty"`
	}
	AxisData struct {
		Axis  competency.Axis `json:",omitempty"`
		Value int             `json:",omitempty"`
	}
	// RegularOutsourcing レギュラー契約条件
	RegularOutsourcing struct {
		Fee                int
		ContractPeriod     int
		MonthlyWorkingTime float64
		Incentive          int
		MonthlyFee         float64
		HourlyFee          int
		Text               string `json:",omitempty"`
	}
	// SpotOutsourcing スポット契約条件
	SpotOutsourcing struct {
		Fee         int
		WorkingTime float64
		HourlyFee   int
		Text        string `json:",omitempty"`
	}
	// OutsourcingAppeal 業務委託ポジションの訴求ポイント
	OutsourcingAppeal struct {
		ExperienceNotEssential bool // 未経験歓迎 false: 選択なし, true: 選択中
		WeekendWorker          bool // 土日稼働可能 false: 選択なし, true: 選択中
		RemoteWorkType         *int // リモートワーク可能 null: 選択なし, 1: 選択中かつ来社不要, 2: 選択中かつ一部出勤
		TransportationPayment  bool // 交通費支給あり false: 選択なし, true: 選択中
		DailyWage              *int // 日給OOO円以上可能 null: 選択なし, int: 選択中かつ日給金額
		OnlineInterview        bool // オンライン面談可能 false: 選択なし, true: 選択中
		ShortTimeWorker        bool // 隙間時間での稼働 false: 選択なし, true: 選択中
		DailyPayment           bool // 即日払い false: 選択なし, true: 「可能」を選択中
		WorkTimeNegotiable     bool // 稼働時間応談 false: 選択なし, true: 「可能」を選択中
		WorkType               *int // 業務内容 false:実務 true:業務支援 2:情報収集
	}
	// Image 掲載画像
	Image struct {
		DisplayType int    // 1:メイン画像、2:サブ画像
		FilePath    string // S3オブジェクトのファイルパス (URLのパス部分と一致する)
	}
	Images []Image

	Positions []*Position
)

const (
	PublishTypePrivate PublishStatus = 0 // 非公開
	PublishTypePublish PublishStatus = 1 // 公開

	OutsourcingRemoteWorkOkFully = 1
)

func (*Position) TableName() string {
	return "user_apply.position"
}

func (p *Position) GetHREvaluationCompetency() map[competency.Axis]competency.EvalCompetencyValue {
	if p.HREvaluationCompetency == nil {
		return nil
	}
	ret := make(map[competency.Axis]competency.EvalCompetencyValue, len(p.HREvaluationCompetency.Axes))
	for _, axe := range p.HREvaluationCompetency.Axes {
		ret[axe.Axis] = competency.EvalCompetencyValue(axe.Value)
	}
	return ret
}

func (i *ModelAnnualIncome) toMap() map[string]int {
	if i == nil {
		return nil
	}
	ret := map[string]int{}
	if i.Income20s != 0 {
		ret[master.ModelAnnualIncomeTwenties] = i.Income20s
	}
	if i.Income30s != 0 {
		ret[master.ModelAnnualIncomeThirties] = i.Income30s
	}
	if i.Income40s != 0 {
		ret[master.ModelAnnualIncomeForties] = i.Income40s
	}
	return ret
}

func (t *HREvaluationType) toMap() map[string]int {
	if t == nil {
		return nil
	}
	ret := map[string]int{}
	if t.Type1 != 0 {
		ret[master.HREvaluationTypeGroup1] = t.Type1
	}
	if t.Type2 != 0 {
		ret[master.HREvaluationTypeGroup2] = t.Type2
	}

	if t.Type3 != 0 {
		ret[master.HREvaluationTypeGroup3] = t.Type3
	}

	if t.Type4 != 0 {
		ret[master.HREvaluationTypeGroup4] = t.Type4
	}
	return ret
}

func (j *Jobs) GetSkillIDs() []int {
	if j == nil {
		return nil
	}
	ret := []int{}
	for _, job := range *j {
		if !job.HasSkills {
			continue
		}
		for _, skill := range job.SkillGroups {
			for _, s := range skill.Skills {
				ret = append(ret, s.ID)
			}
		}
	}
	return ret
}

// GetMain メイン職種を返す
func (j *Jobs) GetMain() *Job {
	if j == nil {
		return nil
	}
	for _, job := range *j {
		if job.Main {
			return &job
		}
	}

	return nil
}

// GetJobTypSmallIDs 職種小を返す
func (j *Jobs) GetJobTypSmallIDs() mapset.Set[master.JobTypeSmallID] {
	if j == nil {
		return mapset.NewThreadUnsafeSet[master.JobTypeSmallID]()
	}

	return miidasMapset.NewThreadUnsafeSetWithTransform(*j, func(job Job) master.JobTypeSmallID {
		return job.SmallID
	})
}

// GetJobTypMiddleIDs 職種中を返す
func (j *Jobs) GetJobTypMiddleIDs() mapset.Set[master.JobTypeMiddleID] {
	if j == nil {
		return mapset.NewThreadUnsafeSet[master.JobTypeMiddleID]()
	}

	return miidasMapset.NewThreadUnsafeSetWithTransform(*j, func(job Job) master.JobTypeMiddleID {
		return job.JobTypeMiddleID()
	})
}

// GetJobTypLargeIDs 職種大を返す
func (j *Jobs) GetJobTypLargeIDs() mapset.Set[master.JobTypeLargeID] {
	if j == nil {
		return mapset.NewThreadUnsafeSet[master.JobTypeLargeID]()
	}

	return miidasMapset.NewThreadUnsafeSetWithTransform(*j, func(job Job) master.JobTypeLargeID {
		return job.JobTypeLargeID()
	})
}

func (p *Position) GetSkillIDs() []int {
	return p.Jobs.GetSkillIDs()
}

func (p *Position) GetJobTypeSmalls() []Job {
	return p.Jobs
}

func (p *Position) GetOvertimeAvg() *int {
	return p.OvertimeAvg.GetIntPtr()
}

func (p *Position) GetBonusCount() *int {
	return p.BonusCount.GetIntPtr()
}

func (p *Position) GetPromotionCount() *int {
	return p.PromotionCount.GetIntPtr()
}

func (p *Position) GetWorkingEnvironments() []int {
	return p.WorkingEnvironment.GetIntIDs()
}

func (p *Position) GetRemoteWork() *int {
	if p.RemoteWork == nil {
		return nil
	}
	return lo.ToPtr(p.RemoteWork.ID)
}

func (p *Position) CanRemoteWork() *bool {
	if p.IsRegular() || p.IsSpot() {
		return lo.ToPtr(p.OutsourcingAppeal.CanRemoteWork())
	}

	value := p.GetRemoteWork()
	if value == nil {
		return nil
	}

	ret := *value != master.RemoteWorkNg
	return &ret
}

func (p *Position) IsRemoteWorkOkFully() *bool {
	if p.IsRegular() || p.IsSpot() {
		return lo.ToPtr(p.OutsourcingAppeal.IsRemoteWorkOkFully())
	}

	value := p.GetRemoteWork()
	if value == nil {
		return nil
	}

	return lo.ToPtr(*value == master.RemoteWorkOkFully)
}

func (p *Position) GetRemoteWorkOfficeFrequency() *int {
	if p.RemoteWorkOfficeFrequency == nil {
		return nil
	}
	return p.RemoteWorkOfficeFrequency.GetIntPtr()
}

// Deprecated: GetIncomeFrom NW以降では使用しない
func (p *Position) GetIncomeFrom() *int {
	panic("GetIncomeFromを呼び出すのはNG.")
}

// Deprecated: GetIncomeTo NW以降では使用しない
func (p *Position) GetIncomeTo() *int {
	panic("GetIncomeToを呼び出すのはNG.")
}

func (p *Position) GetEmploymentTypeID() *int {
	return p.EmploymentType.GetIntPtr()
}

func (p *Position) GetModelAnnualIncome() map[string]int {
	return p.ModelAnnualIncome.toMap()
}

func (p *Position) GetTransferenceExists() *int {
	return p.TransferenceExists.GetIntPtr()
}

func (p *Position) GetTransferenceFrequency() *int {
	return p.TransferenceFrequency.GetIntPtr()
}

func (p *Position) GetTransferenceAbroadExists() *int {
	return p.TransferenceAbroadExists.GetIntPtr()
}

func (p *Position) GetTransferenceAbroadEnglish() *int {
	return p.TransferenceAbroadEnglishIsUnused.GetIntPtr()
}

func (p *Position) GetOfficialTripFrequency() *int {
	return p.OfficialTripFrequency.GetIntPtr()
}

func (p *Position) GetEmploymentToRegularEmployee() *int {
	return p.EmploymentToRegularEmployee.GetIntPtr()
}

func (p *Position) GetEmploymentTypeChange() *int {
	return p.EmploymentTypeChange.GetIntPtr()
}

func (p *Position) GetPost() *int {
	return p.Post.GetIntPtr()
}

func (p *Position) GetWorkTime() *int {
	return p.WorkTimeSystem.GetIntPtr()
}

func (p *Position) GetOutsourcingWorkTime() *float64 {
	if !p.IsOutsourcing() || p.IsCommission() { // 完全歩合は稼働時間の概念がない
		return nil
	}

	var hours float64
	if p.RegularOutsourcing != nil {
		hours = p.RegularOutsourcing.MonthlyWorkingTime
	} else if p.SpotOutsourcing != nil {
		hours = p.SpotOutsourcing.WorkingTime
	}
	return &hours
}

func (p *Position) GetOutsourcingHourlyFee() *int {
	if p.RegularOutsourcing != nil {
		return &p.RegularOutsourcing.HourlyFee
	}
	if p.SpotOutsourcing != nil {
		return &p.SpotOutsourcing.HourlyFee
	}
	return nil
}

func (p *Position) GetWorkTimeNightShift() *int {
	return p.WorkTimeNightsShift.GetIntPtr()
}

func (p *Position) GetHoliday() *int {
	return p.Holiday.GetIntPtr()
}

func (p *Position) GetStockOption() *int {
	return p.StockOption.GetIntPtr()
}

func (p *Position) GetSmokeFreeEnvironment() *int {
	return p.SmokeFreeEnvironment.GetIntPtr()
}

func (p *Position) GetProbation() *int {
	return p.Probation.GetIntPtr()
}

func (p *Position) GetHREvaluationType() map[string]int {
	return p.HREvaluationType.toMap()
}

func (p *Position) GetBaseMonthlySalary() *int {
	return p.BaseMonthlySalary.GetIntPtr()
}

func (p *Position) GetAccomplishmentImportance() *int {
	return p.AccomplishmentImportance.GetIntPtr()
}

func (p *Position) GetAccomplishmentRate() *int {
	return p.AccomplishmentRate.GetIntPtr()
}

func (p *Position) GetSalesStyleDive() *int {
	return p.SalesStyleDive.GetIntPtr()
}

func (p *Position) GetSalesStyleTelAppointment() *int {
	return p.SalesStyleTelAppointment.GetIntPtr()
}

func (p *Position) GetSalesStyleHost() *int {
	return p.SalesStyleHost.GetIntPtr()
}

func (p *Position) GetCareerPathOutOfSiteExists() *int {
	return p.CareerPathOutOfSiteExists.GetIntPtr()
}

func (p *Position) GetCareerPathWorkHeadOfficeExists() *int {
	return p.CareerPathOutOfSiteExists.GetIntPtr()
}

func (p *Position) GetOrgTrendEngineerManagerExists() *int {
	return p.OrgTrendEngineerManagerExists.GetIntPtr()
}

func (p *Position) GetOrgTrendAccountingLicenceExists() *int {
	return p.OrgTrendAccountingLicenceExists.GetIntPtr()
}

func (p *Position) GetOrgTrendLegalLicenceExists() *int {
	return p.OrgTrendLegalLicenceExists.GetIntPtr()
}

func (p *Position) GetOrgTrendRelatedWithEngineer() *int {
	return p.OrgTrendRelatedWithEngineer.GetIntPtr()
}

func (p *Position) GetWorkEnvironment() []int {
	return p.WorkEnvironment.GetIntIDs()
}

func (p *Position) GetDevelopmentTerm() *int {
	return p.DevelopmentTerm.GetIntPtr()
}

func (p *Position) GetDevelopmentProcess() *int {
	return p.DevelopmentProcess.GetIntPtr()
}

func (p *Position) GetEmergencySupport() *int {
	return p.EmergencySupport.GetIntPtr()
}

// LastModifiedAtEqual LastModifiedAt と 与えられた日時が等しいか
func (p *Position) LastModifiedAtEqual(t time.Time) bool {
	return p.LastModifiedAt.Equal(t)
}

// IsJobChange 転職ポジション（正社員・契約社員）
func (p *Position) IsJobChange() bool {
	if p.EmploymentType == nil {
		return false
	}
	return master.PositionEmploymentTypeID(p.EmploymentType.ID).IsJobChange()
}

// IsRegular レギュラーポジション
func (p *Position) IsRegular() bool {
	if p.EmploymentType == nil {
		return false
	}

	return master.PositionEmploymentTypeID(p.EmploymentType.ID).IsRegular()
}

// IsSpot スポットポジション
func (p *Position) IsSpot() bool {
	if p.EmploymentType == nil {
		return false
	}

	return master.PositionEmploymentTypeID(p.EmploymentType.ID).IsSpot()
}

// IsCommission 完全歩合制ポジション
func (p *Position) IsCommission() bool {
	if p.EmploymentType == nil {
		return false
	}

	return master.PositionEmploymentTypeID(p.EmploymentType.ID).IsCommission()
}

// IsAutoSetting 自動オファー送信中であるかどうか
func (p *Position) IsAutoSetting() bool {
	return p.AutoOfferStatus == AutoOfferStatusSending
}

// IsOutsourcing レギュラー・スポット・完全歩合制ポジションのいずれか
func (p *Position) IsOutsourcing() bool {
	if p.EmploymentType == nil {
		return false
	}
	return master.PositionEmploymentTypeID(p.EmploymentType.ID).IsOutsourcing()
}

func (p *Position) GetPublishType() PublishStatus {
	if p.PublishedAt == nil {
		return PublishTypePrivate
	} else {
		return PublishTypePublish
	}
}

// IsPublished 公開されているか
// 公開: true
// 非公開: false
func (p *Position) IsPublished() bool {
	if p == nil {
		return false
	}
	if p.BackwardCompatibleType == BackwardCompatibleTypeInvalid {
		return false
	}
	status := p.GetPublishType()
	return status == PublishTypePublish
}

// HasPublish 公開実績があるか
func (p *Position) HasPublish() bool {
	return p.FirstPublishedAt != nil
}

const (
	constInJapan                master.WorkAddressID = 1000000 // 国内判定用
	constPrefecture             master.WorkAddressID = 10000   // 都道府県ID算出用
	workAddressOverseas         master.WorkAddressID = 9000000 // 海外
	menkakuCancelLimitationDays int                  = 7       // 面確解除不可能な日数(≒オファー自動送信解除不可の日数)
	outsourcingLongTermMonths   int                  = 3       // 業務委託ポジションで長期契約と判断する初回契約期間
)

// IsLongTermOutsourcing は初回契約期間が長期かどうかを返す
//
// 契約延長は考慮に含まれない
// 完全歩合は常に長期とみなされる
func (p *Position) IsLongTermOutsourcing() bool {
	if !p.IsOutsourcing() {
		return false
	}

	if p.IsCommission() {
		return true
	}

	if p.RegularOutsourcing != nil && p.RegularOutsourcing.ContractPeriod >= outsourcingLongTermMonths {
		return true
	}
	return false
}

func (p *Position) IsContractExtensionOk() bool {
	return p.Detail.ContractExtension != nil && p.Detail.ContractExtension.ID == master.ContractExtensionOk
}

func (d *Detail) Scan(value any) error {
	return serializer.JsoniterJSONScan(d, value)
}

func (d Detail) Value() (driver.Value, error) {
	return serializer.StdJSONValue(d)
}

func (p *Position) GetTitle() string {
	return p.Detail.Title
}

func (p *Position) IsTrashed() bool {
	return p.TrashedAt != nil
}

func (p *Position) GetMainImage() *Image {
	for _, image := range p.Images {
		if image.DisplayType == 1 {
			return &image
		}
	}
	return nil
}

func (d *Detail) HasBusiness() bool {
	if d == nil {
		return false
	}
	return d.BusinessID != 0
}

// IsOverseas 海外かどうか
func (w WorkAddress) IsOverseas() bool {
	return w.ID == workAddressOverseas
}

// IsInJapan 国内かどうか
func (w WorkAddress) IsInJapan() bool {
	return w.ID != workAddressOverseas // 海外以外は全て国内
}

// PrefectureID 都道府県IDを取得
// 海外だった場合はエラー
func (w WorkAddress) PrefectureID() (master.PrefectureID, error) {
	if !w.IsInJapan() {
		return 0, errors.New("this work_address is not in japan")
	}
	return master.PrefectureID((w.ID - constInJapan) / constPrefecture), nil
}

// CityID 市区町村コードを取得
// 市区町村の指定なしの場合、0
// 海外だった場合はエラー
func (w WorkAddress) CityID() (master.CityID, error) {
	if ok, err := w.IsCityCodeAssigned(); !ok || err != nil {
		return 0, err
	}
	return master.CityID(w.ID - constInJapan), nil
}

// IsCityCodeAssigned 市区町村コードまで指定しているかどうか
// 海外だった場合はエラー
func (w WorkAddress) IsCityCodeAssigned() (bool, error) {
	if !w.IsInJapan() {
		return false, errors.New("this work_address is not in japan")
	}
	return w.ID%constPrefecture != 0, nil
}

func (wa WorkAddresses) IsIncludeOverSeas() bool {
	for _, w := range wa.Values {
		if w.IsOverseas() {
			return true
		}
	}
	return false
}

func (j *Job) JobTypeLargeID() master.JobTypeLargeID {
	return j.SmallID.JobTypeLargeID()
}

func (j *Job) JobTypeMiddleID() master.JobTypeMiddleID {
	return j.SmallID.JobTypeMiddleID()
}

func (j *Job) GetSkillIDs() []int {
	var ret []int
	for _, skg := range j.SkillGroups {
		for _, skill := range skg.Skills {
			ret = append(ret, skill.ID)
		}
	}
	return ret
}

// GetMenkakuConnectLimitationDays 面確解除不可能な日数(≒オファー自動送信解除不可の日数)
func GetMenkakuConnectLimitationDays() int {
	return menkakuCancelLimitationDays
}

// IsEmpty レギュラーポジション情報が空かどうか
// 報酬が入力されていなければ他の値もない
func (r *RegularOutsourcing) IsEmpty() bool {
	if r == nil {
		return true
	}

	return r.Fee == 0
}

// IsEmpty スポットポジション情報が空かどうか
// 報酬が入力されていなければ他の値もない
func (s *SpotOutsourcing) IsEmpty() bool {
	if s == nil {
		return true
	}

	return s.Fee == 0
}

func (ps Positions) SelectCompanyIDs() []company.ID {
	ret := make([]company.ID, 0, len(ps))
	for _, p := range ps {
		ret = append(ret, p.CompanyID)
	}
	return lo.Uniq(ret)
}

func (ps Positions) SelectBusinessIDs() []business.ID {
	ret := make([]business.ID, 0, len(ps))
	for _, p := range ps {
		ret = append(ret, p.BusinessID)
	}
	return lo.Uniq(ret)
}

func (gi GuaranteedIncome) ToMap() map[vo2.IncomeID]vo2.FromTo {
	return lo.SliceToMap(gi.Incomes, func(in vo2.Income) (vo2.IncomeID, vo2.FromTo) {
		return in.IncomeID, vo2.FromTo{
			From: in.IncomeFrom,
			To:   in.IncomeTo,
		}
	})
}

func (oa *OutsourcingAppeal) CanRemoteWork() bool {
	if oa == nil || oa.RemoteWorkType == nil {
		return false
	}

	return true
}

func (oa *OutsourcingAppeal) IsRemoteWorkOkFully() bool {
	if oa == nil {
		return false
	}

	return oa.RemoteWorkType != nil && *oa.RemoteWorkType == OutsourcingRemoteWorkOkFully
}

func (j *Jobs) Scan(value any) error {
	return serializer.JsoniterJSONScan(j, value)
}

func (j Jobs) Value() (driver.Value, error) {
	return serializer.StdJSONValue(j)
}

func (oa *OutsourcingAppeal) Scan(value any) error {
	return serializer.JsoniterJSONScan(oa, value)
}

func (oa OutsourcingAppeal) Value() (driver.Value, error) {
	return serializer.StdJSONValue(oa)
}

func (wa *WorkAddresses) Scan(value any) error {
	return serializer.JsoniterJSONScan(wa, value)
}

func (wa WorkAddresses) Value() (driver.Value, error) {
	return serializer.StdJSONValue(wa)
}

func (i *Image) GenerateURL() *string {
	if i == nil {
		return nil
	}

	endpoint, err := ms3.GetUserEndpoint()
	if err != nil {
		return nil
	}
	ret := endpoint.JoinPath(i.FilePath).String()
	return &ret
}
