package contracts

import (
	address "aica/api/api/mcptool/usecase/shared"
	"aica/api/domain/public/master"
	"miidas/m2/user/marketvalue/grpc/iface"
)

// 休日
type DayOffLabel string

const (
	DAYOFF_WEEKEND        DayOffLabel = "土日祝休み"
	DAYOFF_TWICE_PER_WEEK DayOffLabel = "毎週2日休み"
	DAYOFF_OTHER          DayOffLabel = "その他"
)

// 残業時間
type OvertimeLabel string

const (
	OVERTIME_NONE             OvertimeLabel = "原則なし"
	OVERTIME_10_HOURS_OR_LESS OvertimeLabel = "10時間以内"
)

// ポジション提案のテーマ
type PositionRecommendationTheme string

const (
	THEME_HIGH_SALARY               PositionRecommendationTheme = "theme1"
	THEME_LITTLE_OVERTIME           PositionRecommendationTheme = "theme2"
	THEME_MISSION_DRIVEN_MANAGEMENT PositionRecommendationTheme = "theme3"
	THEME_HIGH_RETENTION_RATE       PositionRecommendationTheme = "theme4"
	THEME_PARENTAL_LEAVE            PositionRecommendationTheme = "theme5"
	THEME_MATERNITY_LEAVE           PositionRecommendationTheme = "theme6"
	THEME_EMPLOYEE_FRIENDLY         PositionRecommendationTheme = "theme7"
	THEME_FEMALE_EMPLOYEE_RATIO     PositionRecommendationTheme = "theme8"
	THEME_FLEX_TIME                 PositionRecommendationTheme = "theme9"
)

const (
	ToolNameSearchJobPostings                       = "search_job_postings"
	ToolNameSearchJobPostingsForITEngineer          = "search_job_postings_for_it_engineer"
	ToolNameSearchJobPostingsForSalesFinancialSales = "search_job_postings_for_sales_financial_sales"
	SelectedFilterOptionsCommonKey                  = "common"
)

func ToolNameByJobTypeLargeID(jobTypeLargeID master.JobTypeLargeID) string {
	switch jobTypeLargeID {
	case master.JobTypeLargeIDITSpecialist:
		return ToolNameSearchJobPostingsForITEngineer
	case master.JobTypeLargeIDFinancialSpecialist:
		return ToolNameSearchJobPostingsForSalesFinancialSales
	default:
		return ""
	}
}

type (
	JobSpecificSearchResolver interface {
		ExistsPrefectureCity(prefectureName string, cityName string) bool
		ResolveJobTypeSmallIDs(names []string) ([]int32, error)
		ResolveLocations(locations []*address.LocationRequest, remoteWorkPossible bool) ([]int32, *address.LocationRequest, []*address.LocationRequest, []*address.LocationRequest, error)
		ResolveLocationByName(name string) (*address.LocationRequest, error)
		ResolveSkills(skillNames []string) (master.Skills, error)
		ResolveDayOffs(dayOffs *[]string) ([]int32, error)
		ResolveAverageOvertime(overtime *string) (int32, error)
		ResolveSalesStyleDive(salesStyleDive *string) (int32, error)
	}

	PositionSearchWill struct {
		JobTypeLargeID  int32   // 希望職種（大）ID
		JobTypeSmallIDs []int32 // 希望職種（小）ID
		Salary          int32   // 希望年収（万円）
		CityIDs         []int32 // 場所 （居住地または希望勤務地またはフルリモート）
		DayOffs         []int32 // 休日
		AverageOvertime int32   // 平均残業時間
	}

	// JobSpecificSearchInput は職種特化検索（非テーマ）の入力
	JobSpecificSearchInput struct {
		JobTypeLargeID           master.JobTypeLargeID
		JobTypeNames             []string
		SelectedFilterOptionsKey string
		Salary                   int32
		Locations                []*address.LocationRequest
		DayOffs                  *[]string
		AverageOvertime          *string
		Custom                   JobSpecificParams
	}

	JobSpecificParams interface {
		BuildExtensions(resolver JobSpecificSearchResolver) ([]SearchExtension, error)
		SelectedOptionNamesByFilter() map[string]map[string]struct{}
		RemotePositionOptionState() *RemotePositionOptionState
	}

	SearchExtension interface {
		ApplyMV2(companyWill *iface.Company, businessWill *iface.Business, positionWill *iface.Position)
		BuildSelectedOtherFilterOptions() (string, []string)
	}

	KeywordCarrier interface {
		Keyword() string
	}

	RemoteWorkCarrier interface {
		RemoteWorkPossible() bool
	}

	RemotePositionOptionState struct {
		HasOption     bool
		CurrentChoice bool
	}
)
