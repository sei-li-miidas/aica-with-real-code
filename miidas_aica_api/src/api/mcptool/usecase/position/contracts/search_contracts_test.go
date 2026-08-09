package contracts

import "testing"

func TestSearchContracts_ThemeConstants(t *testing.T) {
	themes := []PositionRecommendationTheme{
		THEME_HIGH_SALARY,
		THEME_LITTLE_OVERTIME,
		THEME_MISSION_DRIVEN_MANAGEMENT,
		THEME_HIGH_RETENTION_RATE,
		THEME_PARENTAL_LEAVE,
		THEME_MATERNITY_LEAVE,
		THEME_EMPLOYEE_FRIENDLY,
		THEME_FEMALE_EMPLOYEE_RATIO,
		THEME_FLEX_TIME,
	}
	if len(themes) != 9 {
		t.Fatalf("unexpected theme constants")
	}
}
