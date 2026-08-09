package builder

import (
	pcontracts "aica/api/api/mcptool/usecase/position/contracts"
	"testing"

	"miidas/m2/user/marketvalue/grpc/iface"

	"github.com/stretchr/testify/assert"
)

func TestBuildCompanyWill(t *testing.T) {
	testcases := []struct {
		name     string
		theme    pcontracts.PositionRecommendationTheme
		expected *iface.Company
	}{
		{
			name:  "theme mission driven management",
			theme: pcontracts.THEME_MISSION_DRIVEN_MANAGEMENT,
			expected: &iface.Company{
				AppealPoint:        &iface.AppealPoint{Importance: 3, Value: []int32{13}},
				YearHolidays:       &iface.YearHolidays{Importance: 0},
				WelfareAchievement: &iface.WelfareAchievement{Importance: 0},
				Vacations:          &iface.Vacations{Importance: 0},
			},
		},
		{
			name:  "theme high retention rate",
			theme: pcontracts.THEME_HIGH_RETENTION_RATE,
			expected: &iface.Company{
				AppealPoint:        &iface.AppealPoint{Importance: 3, Value: []int32{6}},
				YearHolidays:       &iface.YearHolidays{Importance: 0},
				WelfareAchievement: &iface.WelfareAchievement{Importance: 0},
				Vacations:          &iface.Vacations{Importance: 0},
			},
		},
		{
			name:  "theme parental leave",
			theme: pcontracts.THEME_PARENTAL_LEAVE,
			expected: &iface.Company{
				AppealPoint:  &iface.AppealPoint{Importance: 0},
				YearHolidays: &iface.YearHolidays{Importance: 0},
				WelfareAchievement: &iface.WelfareAchievement{
					Importance: 3,
					Value:      []int32{1, 2, 4, 5},
				},
				Vacations: &iface.Vacations{Importance: 0},
			},
		},
		{
			name:  "theme maternity leave",
			theme: pcontracts.THEME_MATERNITY_LEAVE,
			expected: &iface.Company{
				AppealPoint:        &iface.AppealPoint{Importance: 0},
				YearHolidays:       &iface.YearHolidays{Importance: 0},
				WelfareAchievement: &iface.WelfareAchievement{Importance: 0},
				Vacations:          &iface.Vacations{Importance: 3, Value: []int32{9, 5, 6, 8}},
			},
		},
		{
			name:  "theme employee friendly",
			theme: pcontracts.THEME_EMPLOYEE_FRIENDLY,
			expected: &iface.Company{
				AppealPoint:        &iface.AppealPoint{Importance: 3, Value: []int32{7, 8}},
				YearHolidays:       &iface.YearHolidays{Importance: 0},
				WelfareAchievement: &iface.WelfareAchievement{Importance: 0},
				Vacations:          &iface.Vacations{Importance: 0},
			},
		},
	}

	for _, tc := range testcases {
		t.Run(tc.name, func(t *testing.T) {
			actual := BuildCompanyWill(tc.theme)

			assert.Equal(t, tc.expected.YearHolidays.Importance, actual.YearHolidays.Importance)
			assert.Equal(t, tc.expected.YearHolidays.Value, actual.YearHolidays.Value)
			assert.Equal(t, tc.expected.AppealPoint.Importance, actual.AppealPoint.Importance)
			assert.Equal(t, tc.expected.AppealPoint.Value, actual.AppealPoint.Value)
			assert.Equal(t, tc.expected.WelfareAchievement.Importance, actual.WelfareAchievement.Importance)
			assert.Equal(t, tc.expected.WelfareAchievement.Value, actual.WelfareAchievement.Value)
			assert.Equal(t, tc.expected.Vacations.Importance, actual.Vacations.Importance)
			assert.Equal(t, tc.expected.Vacations.Value, actual.Vacations.Value)
		})
	}
}

func TestCreateBasePositionWill_WorkAddress(t *testing.T) {
	will := &pcontracts.PositionSearchWill{
		CityIDs: []int32{13101},
	}

	positionWill := CreateBasePositionWill(will)

	assert.Equal(t, int32(0), positionWill.RemoteWork.Importance)
	assert.Nil(t, positionWill.RemoteWork.Value)
	assert.Equal(t, int32(3), positionWill.WorkAddress.Importance)
	assert.Equal(t, []int32{13101}, positionWill.WorkAddress.Value.Cities)
	assert.Nil(t, positionWill.SalesStyleDive)
}

func TestCreateWillForTheme_CoversThemeBuilders(t *testing.T) {
	company := CreateCompanyWillForTheme(&pcontracts.PositionSearchWill{}, pcontracts.THEME_MISSION_DRIVEN_MANAGEMENT)
	assert.Equal(t, int32(3), company.AppealPoint.Importance)

	business := CreateBusinessWillForTheme(&pcontracts.PositionSearchWill{}, pcontracts.THEME_FEMALE_EMPLOYEE_RATIO)
	assert.Equal(t, int32(3), business.EmployeeWomanRate.Importance)

	position := CreatePositionWillForTheme(&pcontracts.PositionSearchWill{Salary: 450}, pcontracts.THEME_HIGH_SALARY)
	assert.Equal(t, int32(3), position.GuaranteedIncome.Importance)
	assert.True(t, *position.GuaranteedIncome.Value > 450)
}

func TestCreateBasePositionWill_AllFields(t *testing.T) {
	will := &pcontracts.PositionSearchWill{
		Salary:          600,
		CityIDs:         []int32{13101},
		JobTypeSmallIDs: []int32{10, 20},
		DayOffs:         []int32{1, 2},
		AverageOvertime: 2,
	}
	positionWill := CreateBasePositionWill(will)
	assert.Equal(t, int32(3), positionWill.WorkAddress.Importance)
	assert.Equal(t, []int32{13101}, positionWill.WorkAddress.Value.Cities)
	assert.Equal(t, int32(3), positionWill.GuaranteedIncome.Importance)
	assert.Equal(t, int32(600), *positionWill.GuaranteedIncome.Value)
	assert.Equal(t, int32(3), positionWill.Job.Importance)
	assert.Equal(t, []int32{10, 20}, positionWill.Job.Value.Smalls)
	assert.Equal(t, int32(3), positionWill.Holiday.Importance)
	assert.Equal(t, []int32{1, 2}, positionWill.Holiday.Value)
	assert.Equal(t, int32(3), positionWill.OvertimeAvg.Importance)
	assert.Equal(t, int32(2), *positionWill.OvertimeAvg.Value)
}

func TestApplyPositionTheme_AllBranches(t *testing.T) {
	t.Run("高年収の場合", func(t *testing.T) {
		p := NewBasePositionWill()
		ApplyPositionTheme(p, pcontracts.THEME_HIGH_SALARY, 400)
		assert.Equal(t, int32(3), p.GuaranteedIncome.Importance)
	})
	t.Run("フレックスタイムの場合", func(t *testing.T) {
		p := NewBasePositionWill()
		ApplyPositionTheme(p, pcontracts.THEME_FLEX_TIME, 400)
		assert.Equal(t, int32(3), p.WorkingEnvironment.Importance)
		assert.Equal(t, []int32{1, 2, 12}, p.WorkingEnvironment.Value)
	})
	t.Run("残業が少ない場合", func(t *testing.T) {
		p := NewBasePositionWill()
		ApplyPositionTheme(p, pcontracts.THEME_LITTLE_OVERTIME, 400)
		assert.Equal(t, int32(3), p.OvertimeAvg.Importance)
		assert.Equal(t, int32(2), *p.OvertimeAvg.Value)
	})
}
