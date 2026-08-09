package builder

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	psupport "aica/api/api/mcptool/usecase/position/support"
	"miidas/m2/user/marketvalue/grpc/iface"
)

func CreateBaseCompanyWill(_ *pcontracts.PositionSearchWill) *iface.Company {
	// 企業情報の検索条件
	companyWill := &iface.Company{
		YearHolidays: &iface.YearHolidays{
			Importance: 0,
		},
		AppealPoint: &iface.AppealPoint{
			Importance: 0,
		},
		WelfareAchievement: &iface.WelfareAchievement{
			Importance: 0,
		},
		Vacations: &iface.Vacations{
			Importance: 0,
		},
	}

	return companyWill
}

func CreateCompanyWillForTheme(will *pcontracts.PositionSearchWill, theme pcontracts.PositionRecommendationTheme) *iface.Company {
	companyWill := CreateBaseCompanyWill(will)
	ApplyCompanyTheme(companyWill, theme)
	return companyWill
}

func CreateBaseBusinessWill(_ *pcontracts.PositionSearchWill) *iface.Business {

	// 事業情報の検索条件
	businessWill := &iface.Business{
		Industry: &iface.Industry{
			Importance: 0,
		},
		EmployeeWomanRate: &iface.EmployeeWomanRate{
			Importance: 0,
		},
	}

	return businessWill
}

func CreateBusinessWillForTheme(will *pcontracts.PositionSearchWill, theme pcontracts.PositionRecommendationTheme) *iface.Business {
	businessWill := CreateBaseBusinessWill(will)
	ApplyBusinessTheme(businessWill, theme)
	return businessWill
}

func CreateBasePositionWill(will *pcontracts.PositionSearchWill) *iface.Position {
	positionWill := NewBasePositionWill()

	if len(will.CityIDs) > 0 {
		// 希望勤務地または居住地からの通勤圏の場合
		positionWill.WorkAddress.Importance = 3
		positionWill.WorkAddress.Value.Cities = will.CityIDs
	}

	// 確約年収
	if will.Salary > 0 {
		positionWill.GuaranteedIncome.Importance = 3
		v := int32(will.Salary)
		positionWill.GuaranteedIncome.Value = &v
	}

	// 希望職種
	if len(will.JobTypeSmallIDs) > 0 {
		positionWill.Job.Importance = 3
		positionWill.Job.Value = &iface.JobValue{
			Smalls: will.JobTypeSmallIDs,
		}
	}

	// 休日
	if len(will.DayOffs) > 0 {
		positionWill.Holiday.Importance = 3
		positionWill.Holiday.Value = will.DayOffs
	}

	// 平均残業時間
	if will.AverageOvertime > 0 {
		positionWill.OvertimeAvg.Importance = 3
		v := will.AverageOvertime
		positionWill.OvertimeAvg.Value = &v
	}

	return positionWill
}

func CreatePositionWillForTheme(will *pcontracts.PositionSearchWill, theme pcontracts.PositionRecommendationTheme) *iface.Position {
	// ポジションの検索条件
	positionWill := CreateBasePositionWill(will)

	// テーマ検索であれば、以下の条件で検索する
	// 1. 年収
	// 2. 場所
	// 3. テーマの検索条件
	// その他の検索条件は無視する
	ApplyPositionTheme(positionWill, theme, int(will.Salary))

	return positionWill
}

func BuildCompanyWill(theme pcontracts.PositionRecommendationTheme) *iface.Company {
	companyWill := CreateBaseCompanyWill(nil)
	ApplyCompanyTheme(companyWill, theme)
	return companyWill
}

func ApplyCompanyTheme(companyWill *iface.Company, theme pcontracts.PositionRecommendationTheme) {
	companyAppealPoints := make([]int32, 0)
	switch theme {
	case pcontracts.THEME_MISSION_DRIVEN_MANAGEMENT:
		companyAppealPoints = append(companyAppealPoints, 13)
	case pcontracts.THEME_HIGH_RETENTION_RATE:
		companyAppealPoints = append(companyAppealPoints, 6)
	case pcontracts.THEME_PARENTAL_LEAVE:
		companyWill.WelfareAchievement.Importance = 3
		companyWill.WelfareAchievement.Value = []int32{1, 2, 4, 5}
	case pcontracts.THEME_MATERNITY_LEAVE:
		companyWill.Vacations.Importance = 3
		companyWill.Vacations.Value = []int32{9, 5, 6, 8}
	case pcontracts.THEME_EMPLOYEE_FRIENDLY:
		companyAppealPoints = append(companyAppealPoints, 7, 8)
	}
	if len(companyAppealPoints) > 0 {
		companyWill.AppealPoint.Importance = 3
		companyWill.AppealPoint.Value = companyAppealPoints
	}
}

func ApplyBusinessTheme(businessWill *iface.Business, theme pcontracts.PositionRecommendationTheme) {
	if theme != pcontracts.THEME_FEMALE_EMPLOYEE_RATIO {
		return
	}
	businessWill.EmployeeWomanRate.Importance = 3
	// 30%以上50%未満 4
	// 50%以上 5
	businessWill.EmployeeWomanRate.Value = []int32{4, 5}
}

func NewBasePositionWill() *iface.Position {
	return &iface.Position{
		Job: &iface.Job{
			Importance: 0,
			Value:      &iface.JobValue{},
		},
		WorkAddress: &iface.WorkAddress{
			Importance: 0,
			Value:      &iface.WorkAddressValue{},
		},
		GuaranteedIncome: &iface.GuaranteedIncome{
			Importance: 0,
			Value:      nil,
		},
		RemoteWork: &iface.RemoteWork{
			Importance: 0,
			Value:      nil,
		},
		Holiday: &iface.Holiday{
			Importance: 0,
			Value:      nil,
		},
		OvertimeAvg: &iface.OvertimeAvg{
			Importance: 0,
			Value:      nil,
		},
		WorkingEnvironment: &iface.WorkingEnvironment{
			Importance: 0,
		},
		EmploymentType: &iface.EmploymentType{
			Importance: 3,
			Value:      []int32{1, 2},
		},
	}
}

func ApplyPositionTheme(positionWill *iface.Position, theme pcontracts.PositionRecommendationTheme, salary int) {
	switch theme {
	case pcontracts.THEME_HIGH_SALARY:
		highSalary := psupport.CalculateHighSalary(salary)
		positionWill.GuaranteedIncome.Importance = 3
		v := int32(highSalary)
		positionWill.GuaranteedIncome.Value = &v
	case pcontracts.THEME_FLEX_TIME:
		positionWill.WorkingEnvironment.Importance = 3
		positionWill.WorkingEnvironment.Value = []int32{1, 2, 12}
	case pcontracts.THEME_LITTLE_OVERTIME:
		positionWill.OvertimeAvg.Importance = 3
		v := int32(2)
		positionWill.OvertimeAvg.Value = &v
	}
}
