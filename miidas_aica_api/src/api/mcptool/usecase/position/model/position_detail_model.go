package model

import (
	"time"

	"aica/api/api/mcptool/usecase/shared_dto"
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/business"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
	"aica/api/sdk/vo"
)

type PositionDetail struct {
	Position *DetailPosition
	Company  *DetailCompany
}

type Image struct {
	DisplayType int
	URL         string
}

type DetailPosition struct {
	ID                                position.ID
	CompanyID                         company.ID
	CompanySectionID                  company.SectionID
	BusinessID                        business.ID
	IsDetailShowable                  bool
	CompanyTrashedAt                  *time.Time
	BossTypeScores                    *position.BossList
	PublishStatus                     position.PublishStatus
	Modified                          time.Time
	Title                             string
	Post                              *shared_dto.ValueText
	EmploymentType                    *shared_dto.ValueText
	Images                            []*Image
	Jobs                              []Job
	MainJobText                       string
	ModelAnnualIncome                 *ModelAnnualIncome
	StockOption                       *shared_dto.ValueText
	BonusCount                        *shared_dto.ValueText
	PromotionCount                    *shared_dto.ValueText
	WorkAddress                       *WorkAddresses
	RemoteWork                        *shared_dto.ValueText
	RemoteWorkCondition               string
	RemoteWorkOfficeFrequency         *shared_dto.ValueText
	Holiday                           *shared_dto.ValueText
	WorkTime                          string
	WorkTimeSystem                    *shared_dto.ValueText
	WorkTimeNightsShift               *shared_dto.ValueText
	OvertimeAvg                       *shared_dto.ValueText
	OfficialTripFrequency             *shared_dto.ValueText
	WorkEnvironment                   *shared_dto.ValueTexts
	TransferenceExists                *shared_dto.ValueText
	TransferenceFrequency             *shared_dto.ValueText
	TransferenceAbroadExists          *shared_dto.ValueText
	TransferenceAbroadEnglishIsUnused *shared_dto.ValueText
	HREvaluationType                  *HREvaluationType
	HREvaluationCompetency            *HREvaluationCompetency
	PR                                string
	AccomplishmentImportance          *ValueTextWithOptions
	AccomplishmentRate                *shared_dto.ValueText
	SalesStyleDive                    *shared_dto.ValueText
	SalesStyleTelAppointment          *shared_dto.ValueText
	SalesStyleHost                    *shared_dto.ValueText
	BaseMonthlySalary                 *shared_dto.ValueText
	OvertimeSalary                    *OvertimeSalary
	CareerPathOutOfSiteExists         *shared_dto.ValueText
	CareerPathWorkHeadOfficeExists    *shared_dto.ValueText
	OrgTrendEngineerManagerExists     *shared_dto.ValueText
	OrgTrendSectionMemberQty          *shared_dto.ValueText
	OrgTrendAccountingLicenceExists   *shared_dto.ValueText
	OrgTrendLegalLicenceExists        *shared_dto.ValueText
	OrgTrendRelatedWithEngineer       *shared_dto.ValueText
	ITEngineerWorkEnvironment         *shared_dto.ValuesText
	DevelopmentTerm                   *shared_dto.ValueText
	DevelopmentProcess                *ValueTextWithOptions
	EmergencySupport                  *shared_dto.ValueText
	JoinedReserve                     int
	EmploymentToRegularEmployee       *shared_dto.ValueText
	Probation                         *shared_dto.ValueText
	ContractPeriod                    *shared_dto.ValueText
	ContractRenewal                   *shared_dto.ValueText
	ContractRenewalText               string
	ContractExtension                 *shared_dto.ValueText
	JobChange                         *JobChange
	RegularOutsourcing                *RegularOutsourcing
	SpotOutsourcing                   *SpotOutsourcing
	SpotJobRequest                    *SpotJobRequest `json:"SpotJobRequest,omitempty"`
	SpotJobDescription                string
	SpotExpLevels                     *[]SpotExpLevels `json:"SpotExpLevels,omitempty"`
	CommissionOutsourcing             *CommissionOutsourcing
	EmploymentTypeChange              *shared_dto.ValueText
	OutsourcingAppeal                 *OutsourcingAppeal
	SmokeFree                         *shared_dto.ValueText
	SmokeFreeEnvironment              *shared_dto.ValueText
	Tags                              []position.Tag
	Interview                         *InterviewDetail
}

type DetailCompany struct {
	Withdrawal                  bool
	Name                        string
	IsHPMCertified              bool
	HPMCertificationDisplayYear *int
	IsAgreedHatarakuhitoFirst   bool
}

type InterviewDetail struct {
	Shared         Shared
	Meeting        position.Meeting
	Online         position.Online
	Phone          position.Phone
	WorkExperience WorkExperience
}

type Shared struct {
	EstimatedTerm                string
	InterviewTimes               position.InterviewTimes
	SelectionAptitudeTestExists  bool
	SelectionPaperTestExists     bool
	SelectionPracticalTestExists bool
	SelectionOtherTestExists     bool
	SelectionRemarks             string
	CasualDressFlg               bool
	Interviewers                 []vo.IntIDNamePair
	OtherInterviewer             string
	Contact                      string
}

type WorkExperience struct {
	Pattern          vo.IntIDNamePair
	Timing           vo.IntIDNamePair
	TimingRemarks    string
	OtherTimingText  string
	WorkTypes        vo.IntIDNamePairs
	WorkContent      string
	Timeframe        vo.IntIDNamePair
	TimeframeRemarks string
	NeedTime         vo.IntIDNamePair
	NeedTimeRemarks  string
	Reward           vo.IntIDNamePair
	RewardValue      int
	RewardRemarks    string
}

type ValueTextWithOptions struct {
	ID      int
	Note    string
	Options []shared_dto.IDWithName
}

type JobChange struct {
	Income *IncomeRange
}

type IncomeRange struct {
	From int
	To   int
	Note string
}

type WorkAddresses struct {
	Values []WorkAddress
	Note   string
}

type WorkAddress struct {
	ID       master.WorkAddressID
	Name     string
	Note     string
	Priority int
}

type Job struct {
	SmallID     master.JobTypeSmallID
	Name        string
	Main        bool
	SkillGroups []SkillGroup
}

type SkillGroup struct {
	ID          int
	Name        string
	DummyGroups []DummyGroup
}

type DummyGroup struct {
	Name   string
	Skills []Skill
}

type Skill struct {
	ID   int
	Name string
	Main bool
}

type RegularOutsourcing struct {
	Fee                int
	ContractPeriod     int
	MonthlyWorkingTime float64
	Incentive          int
	MonthlyFee         float64
	HourlyFee          int
	Note               string
}

type CommissionOutsourcing struct {
	Fee                 string
	BusinessDescription string
}

type SpotOutsourcing struct {
	Fee         int
	WorkingTime float64
	HourlyFee   int
	Note        string
}

type SpotJobRequest struct {
	ID                  int
	Name                string
	SpotExpLevelPattern string
}

type SpotExpLevels struct {
	ClassNo int
	List    []shared_dto.IDWithName
}

type OutsourcingAppeal struct {
	ExperienceNotEssential bool
	WeekendWorker          bool
	RemoteWorkType         *int
	TransportationPayment  bool
	DailyWage              *int
	OnlineInterview        bool
	ShortTimeWorker        bool
	DailyPayment           bool
	WorkTimeNegotiable     bool
	WorkType               *int
}

type ModelAnnualIncome struct {
	Income20s int `json:",omitempty"`
	Income30s int `json:",omitempty"`
	Income40s int `json:",omitempty"`
	Note      string
}

type HREvaluationType struct {
	Type1 int `json:",omitempty"`
	Type2 int `json:",omitempty"`
	Type3 int `json:",omitempty"`
	Type4 int `json:",omitempty"`
	Note  string
}

type OvertimeSalary struct {
	HasOvertimeSalary int `json:",omitempty"`
	MonthlyAmount     int `json:",omitempty"`
	ExpectedHours     int `json:",omitempty"`
}

type HREvaluationCompetency struct {
	Axes []position.AxisData
	Note string
}
