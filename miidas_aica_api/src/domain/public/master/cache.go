package master

import (
	"context"
	"errors"

	"github.com/samber/lo"
	"gorm.io/gorm"
	"gorm.io/gorm/schema"

	"aica/api/sdk/gormio"
	mlogger "aica/api/sdk/logger"
	"aica/api/sdk/slice"
	"aica/api/sdk/util"
)

var ErrNoMaster = errors.New("存在しないマスターです")

type Cache struct {
	Cities                                Cities
	DepartmentTypes                       []*DepartmentType
	EmployeeQties                         []*EmployeeQty
	EmploymentTypes                       []*EmploymentType
	ExpCompanies                          []*ExpCompany
	IndustrySmalls                        []*IndustrySmall
	Interviewers                          []*Interviewer
	JobTypeLarges                         []*JobTypeLarge
	JobTypeSmalls                         []*JobTypeSmall
	LangLevels                            []*LangLevel
	ManagementPeopleQties                 []*ManagementPeopleQty
	Prefectures                           Prefectures
	ProfessionalTrainingCollegeCategories []*ProfessionalTrainingCollegeCategory
	SchoolTypes                           []*SchoolType
	Schools                               Schools
	SkillGroups                           []*SkillGroup
	Skills                                []*Skill
	SpotExpLevels                         []*SpotExpLevel
	SpotJobRequests                       []*SpotJobRequest
	TraitBusinessOptions                  map[MasterTraitBusinessID][]*TraitBusinessOption
	TraitCompanyOptions                   map[MasterTraitCompanyID][]*TraitCompanyOption
	TraitPositionOptions                  map[MasterTraitPositionID][]*TraitPositionOption
	WorkExperiencePatterns                []*WorkExperiencePattern
	WorkExperienceTimings                 []*WorkExperienceTiming
	WorkExperienceContentTypes            []*WorkExperienceContentType
	WorkExperienceTimeframes              []*WorkExperienceTimeframe
	WorkExperienceNeedtimes               []*WorkExperienceNeedtime
	WorkExperienceRewards                 []*WorkExperienceReward
	PrefectureCities                      PrefectureCities
}

// newCache キャッシュ生成
func newCache(ctx context.Context, cp gormio.ConnProvider, logger mlogger.LevelLogger) *Cache {
	var c Cache
	LoadCommon(cp(ctx), &c, ctx, logger)
	return &c
}

// LoadCommon 全システム共通で使えるMasterキャッシュを生成する
func LoadCommon(db *gorm.DB, c *Cache, ctx context.Context, logger mlogger.LevelLogger) {
	logger.Info("LoadCommon Start")

	c.Cities = loadByOrder[City](db)
	c.DepartmentTypes = loadByOrder[DepartmentType](db)
	c.EmployeeQties = loadByOrder[EmployeeQty](db)
	c.EmploymentTypes = loadByOrder[EmploymentType](db)
	c.ExpCompanies = loadByOrder[ExpCompany](db)
	c.IndustrySmalls = loadByOrder[IndustrySmall](db)
	c.Interviewers = loadByOrder[Interviewer](db)
	c.JobTypeLarges = loadByOrder[JobTypeLarge](db)
	c.JobTypeSmalls = loadByOrder[JobTypeSmall](db)
	c.LangLevels = loadByOrder[LangLevel](db)
	c.ManagementPeopleQties = loadByOrder[ManagementPeopleQty](db)
	c.Prefectures = loadByOrder[Prefecture](db)
	c.ProfessionalTrainingCollegeCategories = loadByOrder[ProfessionalTrainingCollegeCategory](db)
	c.Schools = loadByOrder[School](db)
	c.SchoolTypes = loadByOrder[SchoolType](db)
	c.SkillGroups = loadByOrder[SkillGroup](db)
	c.Skills = loadByOrder[Skill](db)
	c.SpotExpLevels = loadByOrder[SpotExpLevel](db)
	c.SpotJobRequests = loadByOrder[SpotJobRequest](db)
	c.TraitCompanyOptions = LoadTraitCompanyOptions(db)
	c.TraitBusinessOptions = LoadTraitBusinessOptions(db)
	c.TraitPositionOptions = LoadTraitPositionOptions(db)
	c.WorkExperiencePatterns = loadByOrder[WorkExperiencePattern](db)
	c.WorkExperienceTimings = loadByOrder[WorkExperienceTiming](db)
	c.WorkExperienceContentTypes = loadByOrder[WorkExperienceContentType](db)
	c.WorkExperienceTimeframes = loadByOrder[WorkExperienceTimeframe](db)
	c.WorkExperienceNeedtimes = loadByOrder[WorkExperienceNeedtime](db)
	c.WorkExperienceRewards = loadByOrder[WorkExperienceReward](db)

	c.PrefectureCities = createPrefectureCities(c.Prefectures, c.Cities)

	logger.Info("LoadCommon End")
}

func createPrefectureCities(prefectures Prefectures, cities Cities) PrefectureCities {
	var result PrefectureCities

	for _, city := range cities {
		for _, prefecture := range prefectures {
			if city.PrefectureID == prefecture.ID {
				if city.Name == Tokyo23 {
					for _, tokyo23Ward := range util.GetTokyo23Wards() {
						result = append(result, &PrefectureCity{
							CityID:         city.ID,
							CityName:       city.Name,
							CityKana:       city.Kana,
							RealCityName:   CityName(tokyo23Ward.Name),
							RealCityKana:   tokyo23Ward.Kana,
							PrefectureID:   prefecture.ID,
							PrefectureName: prefecture.Name,
							Name:           prefecture.Name + tokyo23Ward.Name,
							Kana:           prefecture.Name + tokyo23Ward.Kana,
						})
					}
				}

				result = append(result, &PrefectureCity{
					CityID:         city.ID,
					CityName:       city.Name,
					PrefectureID:   prefecture.ID,
					PrefectureName: prefecture.Name,
					Name:           prefecture.Name + string(city.Name),
					Kana:           prefecture.Name + city.Kana,
				})
				break
			}
		}
	}

	return result
}

// Get キャッシュから取得する
func (c *Cache) Get(name string) (any, error) {
	var ret any
	switch name {
	case "City":
		ret = c.Cities
	case "DepartmentType":
		ret = c.DepartmentTypes
	case "EmployeeQty":
		ret = c.EmployeeQties
	case "EmploymentType":
		ret = c.EmploymentTypes
	case "ExpCompany":
		ret = c.ExpCompanies
	case "IndustrySmall":
		ret = c.IndustrySmalls
	case "Interviewer":
		ret = c.Interviewers
	case "JobTypeLarge":
		ret = c.JobTypeLarges
	case "JobTypeSmall":
		ret = c.JobTypeSmalls
	case "LangLevel":
		ret = c.LangLevels
	case "ManagementPeopleQty":
		ret = c.ManagementPeopleQties
	case "Prefecture":
		ret = c.Prefectures
	case "ProfessionalTrainingCollegeCategory":
		ret = c.ProfessionalTrainingCollegeCategories
	case "School":
		ret = c.Schools
	case "SchoolType":
		ret = c.SchoolTypes
	case "SpotJobRequest":
		ret = c.SpotJobRequests
	case "WorkExperiencePattern":
		ret = c.WorkExperiencePatterns
	case "WorkExperienceTiming":
		ret = c.WorkExperienceTimings
	case "WorkExperienceContentType":
		ret = c.WorkExperienceContentTypes
	case "WorkExperienceTimeframe":
		ret = c.WorkExperienceTimeframes
	case "WorkExperienceNeedTime":
		ret = c.WorkExperienceNeedtimes
	case "WorkExperienceReward":
		ret = c.WorkExperienceRewards
	default:
		return nil, ErrNoMaster
	}
	return ret, nil
}

// loadByOrder sort_orderカラムで昇順に並んだリストを返します。
func loadByOrder[T schema.Tabler](db *gorm.DB, scopes ...func(*gorm.DB) *gorm.DB) []*T {
	var ret []*T
	if err := db.Scopes(scopes...).Order("sort_order").Find(&ret).Error; err != nil {
		panic(err)
	}
	return ret
}

func LoadTraitBusinessOptions(db *gorm.DB) map[MasterTraitBusinessID][]*TraitBusinessOption {
	var rows []*TraitBusinessOption
	if err := db.Order("sort_order").Find(&rows).Error; err != nil {
		panic(err)
	}
	return slice.GroupBy(rows, func(_ int, e *TraitBusinessOption) (MasterTraitBusinessID, *TraitBusinessOption) {
		return e.TraitBusinessID, e
	})
}

func LoadTraitCompanyOptions(db *gorm.DB) map[MasterTraitCompanyID][]*TraitCompanyOption {
	var rows []*TraitCompanyOption
	if err := db.Order("sort_order").Find(&rows).Error; err != nil {
		panic(err)
	}
	return slice.GroupBy(rows, func(_ int, e *TraitCompanyOption) (MasterTraitCompanyID, *TraitCompanyOption) {
		return e.TraitCompanyID, e
	})
}

func LoadTraitPositionOptions(db *gorm.DB) map[MasterTraitPositionID][]*TraitPositionOption {
	var rows []*TraitPositionOption
	if err := db.Order("sort_order").Find(&rows).Error; err != nil {
		panic(err)
	}

	ret := lo.GroupBy(rows, func(row *TraitPositionOption) MasterTraitPositionID {
		return row.TraitPositionID
	})

	return ret
}
