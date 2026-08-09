package company

import (
	"database/sql/driver"
	"time"

	"github.com/samber/lo"

	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/vo"
	"aica/api/sdk/gormio/serializer"
)

type (
	// ID 企業ID
	ID            int
	SectionID     int
	CompanyUserID int

	Detail struct {
		Name                         string `json:",omitempty"`
		NameID                       master.CompanyNameID
		Withdrew                     bool
		ProfitCompany                *vo.ValueText             `json:",omitempty"`
		Address                      *Address                  `json:",omitempty"`
		EmployeeQty                  *vo.ValueText             `json:",omitempty"`
		EstablishmentYear            *vo.ValueText             `json:",omitempty"`
		CapitalType                  *vo.ValuesText            `json:",omitempty"`
		SalesScale                   *vo.ValueText             `json:",omitempty"`
		PresidentName                string                    `json:",omitempty"`
		Website                      string                    `json:",omitempty"`
		Introduction                 string                    `json:",omitempty"`
		AppealPoint                  *vo.ValuesText            `json:",omitempty"`
		SalesOverseasRate            *vo.ValueText             `json:",omitempty"`
		EmployeeWorkAbroadRate       *vo.ValueText             `json:",omitempty"`
		WelfareBenefit               vo.ValueTexts             `json:",omitempty"`
		WelfareInsurance             vo.ValueTexts             `json:",omitempty"`
		YearHolidays                 *vo.ValueText             `json:",omitempty"`
		SideBusiness                 *vo.ValueText             `json:",omitempty"`
		SideBusinessCondition        string                    `json:",omitempty"`
		Vacations                    vo.ValueTexts             `json:",omitempty"`
		PaidHolidayUseRate           *vo.ValueText             `json:",omitempty"`
		JobRotationExists            *vo.FlagText              `json:",omitempty"`
		ChangeDepartmentRequest      *vo.FlagText              `json:",omitempty"`
		SpecialistCareerPath         *vo.ValueText             `json:",omitempty"`
		HREvaluationSpecialSystem    *vo.ValuesText            `json:",omitempty"`
		HREvaluationWomanManagerRate *vo.ValueText             `json:",omitempty"`
		HREvaluation20sManagerRate   *vo.ValueText             `json:",omitempty"`
		TrainingSystem               *TrainingSystem           `json:",omitempty"`
		WelfareAchievement           vo.ValueTexts             `json:",omitempty"`
		WelfarePopular               vo.ValueTexts             `json:",omitempty"`
		WelfareOther                 vo.ValueTexts             `json:",omitempty"`
		Other                        *vo.ValuesText            `json:",omitempty"`
		PR                           string                    `json:",omitempty"`
		Document                     []*Document               `json:",omitempty"`
		HPMCompanyDeclaration        string                    `json:",omitempty"`
		HPMCertifiedFrom             *time.Time                `json:",omitempty"`
		HPMCertifiedTo               *time.Time                `json:",omitempty"`
		IsAgreedHatarakuhitoFirst    bool                      `json:",omitempty"`
		RecentHPMCertifications      []*RecentHPMCertification `json:",omitempty"`
	}

	// Company 企業
	Company struct {
		ID ID
		Detail
		IsSearchable         bool
		StopOffer            bool
		StopOfferDatetime    *time.Time
		RegistrationStatusID RegistrationStatus
		LastModifiedAt       time.Time
		ImportedAt           time.Time
	}
	Address struct {
		PrefectureID    int
		PrefectureLabel string `json:",omitempty"`
		Address         string `json:",omitempty"`
	}

	TrainingSystem struct {
		Exists bool
		Text   string `json:",omitempty"`
	}
	Welfare struct {
		Achievement []*vo.ValueText
		Popular     []*vo.ValueText
		Other       []*vo.ValueText
	}

	Document struct {
		ID    int
		Path  string
		Label string
	}

	RecentHPMCertification struct {
		Year int
		From time.Time
		To   time.Time
	}
)

func (*Company) TableName() string {
	return "user_apply.company"
}

func (c *Company) GetEmployeeQtyID() *int {
	return c.EmployeeQty.GetIntPtr()
}

func (c *Company) GetYearHoliday() *int {
	return c.YearHolidays.GetIntPtr()
}

func (c *Company) GetPaidHolidayUseRate() *int {
	return c.PaidHolidayUseRate.GetIntPtr()
}

func (c *Company) GetJobRotationExists() *int {
	return c.JobRotationExists.GetIntPtr()
}

func (c *Company) GetChangeDepartmentRequest() *int {
	return c.ChangeDepartmentRequest.GetIntPtr()
}

func (c *Company) GetHREvaluationSpecialSystem() []int {
	return c.HREvaluationSpecialSystem.GetIntIDs()
}

func (c *Company) GetSpecialistCareerPath() *int {
	return c.SpecialistCareerPath.GetIntPtr()
}

func (c *Company) GetHREvaluationWomanManagerRate() *int {
	return c.HREvaluationWomanManagerRate.GetIntPtr()
}

func (c *Company) GetHREvaluation20SManagerRate() *int {
	return c.HREvaluation20sManagerRate.GetIntPtr()
}

func (c *Company) GetProfitCompany() *int {
	return c.ProfitCompany.GetIntPtr()
}

func (c *Company) GetAddressPrefecture() *int {
	return lo.ToPtr(c.Address.PrefectureID)
}

func (c *Company) GetEstablishmentYear() *int {
	return c.EstablishmentYear.GetIntPtr()
}

func (c *Company) GetCapitalType() []int {
	return c.CapitalType.GetIntIDs()
}

func (c *Company) GetSalesScale() *int {
	return c.SalesScale.GetIntPtr()
}

func (c *Company) GetAppealPoints() []int {
	return c.AppealPoint.GetIntIDs()
}

func (c *Company) GetWelfareBenefits() []int {
	return c.WelfareBenefit.GetIntIDs()
}

func (c *Company) GetWelfareInsurances() []int {
	return c.WelfareInsurance.GetIntIDs()
}

func (c *Company) GetVacations() []int {
	return c.Vacations.GetIntIDs()
}

func (c *Company) GetWelfareAchievements() []int {
	return c.WelfareAchievement.GetIntIDs()
}

func (c *Company) GetWelfarePopular() []int {
	return c.WelfarePopular.GetIntIDs()
}

func (c *Company) GetWelfareOthers() []int {
	return c.WelfareOther.GetIntIDs()
}

func (c *Company) GetEmployeeWorkAbroadRate() *int {
	return c.EmployeeWorkAbroadRate.GetIntPtr()
}

func (c *Company) GetSalesOverseasRate() *int {
	return c.SalesOverseasRate.GetIntPtr()
}

func (c *Company) GetTrainingSystemExists() *int {
	if c.TrainingSystem == nil {
		return nil
	}
	if c.TrainingSystem.Exists {
		return lo.ToPtr(1)
	}
	return lo.ToPtr(0)
}

func (c *Company) GetOther() []int {
	return c.Other.GetIntIDs()
}

func (c *Company) GetSideBusiness() *int {
	return c.SideBusiness.GetIntPtr()
}

func (c *Company) GetDocument(docID int) *Document {
	for _, d := range c.Document {
		if d.ID == docID {
			return d
		}
	}
	return nil
}

func (d *Detail) Scan(value interface{}) error {
	return serializer.JsoniterJSONScan(d, value)
}

func (d Detail) Value() (driver.Value, error) {
	return serializer.StdJSONValue(d)
}

// IsWithdrawn 退会しているか
func (c *Company) IsWithdrawn() bool {
	return c.Detail.Withdrew
}

// 有料企業か（現状はオファー送信可能かのフラグを見ている）
func (c *Company) IsCharged() bool {
	return !c.StopOffer
}

// 健康経営認定企業かどうか
func (c *Company) IsHPMCertified(now time.Time) bool {
	if c == nil {
		return false
	}

	// from,toの未設定は認定企業と認めない
	if c.HPMCertifiedFrom == nil || c.HPMCertifiedTo == nil {
		return false
	}
	// from < now < to かどうか
	return c.HPMCertifiedFrom.Before(now) && c.HPMCertifiedTo.After(now)
}

// 表示する健康経営マークの認定年度
func (c *Company) HPMCertificationDisplayYear() *int {
	if c == nil || len(c.RecentHPMCertifications) == 0 {
		return nil
	}

	var withinCertifiedPeriodYear *int

	now := time.Now()
	for _, rhc := range c.RecentHPMCertifications {
		// 現在時刻が認定期間内のものがあればその認定年度を返す
		if rhc.From.Before(now) && rhc.To.After(now) {
			if withinCertifiedPeriodYear == nil {
				withinCertifiedPeriodYear = &rhc.Year
			}
			if *withinCertifiedPeriodYear < rhc.Year {
				withinCertifiedPeriodYear = &rhc.Year
			}
		}
	}
	return withinCertifiedPeriodYear
}

// IsRegistered 企業登録ステータスが本登録かどうか
func (c *Company) IsRegistered() bool {
	return c.RegistrationStatusID == RegistrationStatusRegistered
}
