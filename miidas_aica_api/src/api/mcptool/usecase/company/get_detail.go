package company

import (
	"fmt"
	"regexp"
	"time"

	"github.com/pkg/errors"

	"aica/api/api/mcptool/usecase/shared_dto"
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
	userMaster "aica/api/domain/user/master"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
)

type GetDetailUseCase struct {
	logger           logger.LevelLogger
	readPositionRepo readPositionRepository
	readCompanyRepo  readCompanyRepository
	readBusinessRepo readBusinessRepository
	prefMaster       prefectureProvider
}

type GetDetailResponse struct {
	ID                           company.ID // ID
	Name                         string     // 企業名
	Prefecture                   string     // 都道府県名
	Address                      string     // 市区町村以下
	OriginalFiles                []Document // オリジナル資料
	BusinessNames                []string   // 事業名
	ProfitCompany                *shared_dto.ValueText
	EmployeeQty                  *shared_dto.ValueText
	EstablishmentYear            *shared_dto.ValueText
	CapitalType                  *shared_dto.ValuesTextWithOptions
	SalesScale                   *shared_dto.ValueText
	PresidentName                string
	Website                      string
	Introduction                 string
	AppealPoint                  *shared_dto.ValuesTextWithOptions
	SalesOverseasRate            *shared_dto.ValueText
	EmployeeWorkAbroadRate       *shared_dto.ValueText
	WelfareBenefit               *shared_dto.ValueTextsWithOptions
	WelfareInsurance             *shared_dto.ValueTextsWithOptions
	YearHolidays                 *shared_dto.ValueText
	SideBusiness                 *shared_dto.ValueText
	SideBusinessCondition        string
	Vacations                    *shared_dto.ValueTextsWithOptions
	PaidHolidayUseRate           *shared_dto.ValueText
	JobRotationExists            *shared_dto.FlagText
	ChangeDepartmentRequest      *shared_dto.FlagText
	SpecialistCareerPath         *shared_dto.ValueText
	HREvaluationSpecialSystem    *shared_dto.ValuesTextWithOptions
	HREvaluationWomanManagerRate *shared_dto.ValueText
	HREvaluation20sManagerRate   *shared_dto.ValueText
	TrainingSystem               *company.TrainingSystem
	WelfareAchievement           *shared_dto.ValueTextsWithOptions
	WelfarePopular               *shared_dto.ValueTextsWithOptions
	WelfareOther                 *shared_dto.ValueTextsWithOptions
	Other                        *shared_dto.ValuesTextWithOptions
	PR                           string
	HPMCompanyDeclaration        string
	IsHPMCertified               bool
	HPMCertificationDisplayYear  *int
	IsAgreedHatarakuhitoFirst    bool
}

type Document struct {
	ID    int
	Label string
}

func NewGetDetailUseCaseWithRepositories(
	l logger.LevelLogger,
	readPositionRepo readPositionRepository,
	readCompanyRepo readCompanyRepository,
	readBusinessRepo readBusinessRepository,
	prefMaster prefectureProvider,
) *GetDetailUseCase {
	return &GetDetailUseCase{
		logger:           l,
		readPositionRepo: readPositionRepo,
		readCompanyRepo:  readCompanyRepo,
		readBusinessRepo: readBusinessRepo,
		prefMaster:       prefMaster,
	}
}

// TODO: 外部公開しないように、レスポンスから各種ID（会社IDなど）を外す。
// Execute .
func (uc *GetDetailUseCase) Execute(positionID position.ID) (*GetDetailResponse, error) {
	companyID, err := uc.readPositionRepo.GetCompanyID(positionID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(errors.WithMessage(err, "企業の取得処理に失敗しました"))
	} else if companyID == nil {
		return nil, merr.ErrResourceNotFound.WithStack()
	}

	c, err := uc.readCompanyRepo.Get(*companyID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(errors.WithMessage(err, "企業の取得処理に失敗しました"))
	} else if c == nil {
		return nil, merr.ErrResourceNotFound.WithStack()
	} else if c.Withdrew || !c.IsSearchable { // 退会済み or 検索不可の場合は見せない
		return nil, merr.ErrResourceNotFound.WithStack()
	}

	// 事業名
	var bNames []string
	bs, err := uc.readBusinessRepo.GetByCompanyID(c.ID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(errors.WithMessage(err, "事業の取得処理に失敗しました"))
	}
	for i := range bs {
		if b := bs[i]; b.IsNotTrashed() {
			bNames = append(bNames, b.Name)
		}
	}

	return buildGetDetailResponse(c, bNames, uc.prefMaster.PrefectureMap()), nil
}

// ユーザー側表示に用いる、ゆるめのURLチェック
var softURLRegexp = regexp.MustCompile(`https?://.+\..+`)

func buildGetDetailResponse(
	c *company.Company,
	bNames []string,
	prefMap master.PrefectureMap,
) *GetDetailResponse {
	h := userMaster.TraitHelper{}
	return &GetDetailResponse{
		ID:                           c.ID,
		Name:                         c.Name,
		Prefecture:                   showPrefecture(master.PrefectureID(c.Address.PrefectureID), prefMap),
		Address:                      showAddress(c.Address, prefMap),
		OriginalFiles:                showDocument(c.Document),
		BusinessNames:                showBusinessNames(bNames),
		ProfitCompany:                shared_dto.ShowValueText(c.ProfitCompany, h.GetCompanyTraitProfitCompany),
		EmployeeQty:                  shared_dto.ShowValueText(c.EmployeeQty, h.GetCompanyTraitEmployeeQty),
		EstablishmentYear:            shared_dto.ShowValueText(c.EstablishmentYear, h.GetCompanyTraitEstablishmentYear),
		CapitalType:                  shared_dto.ShowValuesTextWithOptions(c.CapitalType, h.GetCompanyTraitCapitalTypes()),
		SalesScale:                   shared_dto.ShowValueText(c.SalesScale, h.GetCompanyTraitSalesScale),
		PresidentName:                c.PresidentName,
		Website:                      showWebsite(c.Website),
		Introduction:                 c.Introduction,
		AppealPoint:                  shared_dto.ShowValuesTextWithOptions(c.AppealPoint, h.GetCompanyTraitAppealPoints()),
		SalesOverseasRate:            shared_dto.ShowValueText(c.SalesOverseasRate, h.GetCompanyTraitSalesOverseasRate),
		EmployeeWorkAbroadRate:       shared_dto.ShowValueText(c.EmployeeWorkAbroadRate, h.GetCompanyTraitEmployeeWorkAbroadRate),
		WelfareBenefit:               shared_dto.ShowValueTextsWithOptions(c.WelfareBenefit, h.GetCompanyTraitWelfareBenefits()),
		WelfareInsurance:             shared_dto.ShowValueTextsWithOptions(c.WelfareInsurance, h.GetCompanyTraitWelfareInsurances()),
		YearHolidays:                 shared_dto.ShowValueText(c.YearHolidays, h.GetCompanyTraitYearHolidays),
		SideBusiness:                 shared_dto.ShowValueText(c.SideBusiness, h.GetCompanyTraitSideBusiness),
		SideBusinessCondition:        c.SideBusinessCondition,
		Vacations:                    shared_dto.ShowValueTextsWithOptions(c.Vacations, h.GetCompanyTraitVacationsAll()),
		PaidHolidayUseRate:           shared_dto.ShowValueText(c.PaidHolidayUseRate, h.GetCompanyTraitPaidHolidayUseRate),
		JobRotationExists:            shared_dto.ShowFlagText(c.JobRotationExists, h.GetCompanyTraitJobRotationExists),
		ChangeDepartmentRequest:      shared_dto.ShowFlagText(c.ChangeDepartmentRequest, h.GetCompanyTraitChangeDepartmentRequest),
		SpecialistCareerPath:         shared_dto.ShowValueText(c.SpecialistCareerPath, h.GetCompanyTraitSpecialistCareerPath),
		HREvaluationSpecialSystem:    shared_dto.ShowValuesTextWithOptions(c.HREvaluationSpecialSystem, h.GetCompanyTraitHREvaluationSpecialSystems()),
		HREvaluationWomanManagerRate: shared_dto.ShowValueText(c.HREvaluationWomanManagerRate, h.GetCompanyTraitHREvaluationWomanManagerRate),
		HREvaluation20sManagerRate:   shared_dto.ShowValueText(c.HREvaluation20sManagerRate, h.GetCompanyTraitHREvaluation20sManagerRate),
		TrainingSystem:               c.TrainingSystem,
		WelfareAchievement:           shared_dto.ShowValueTextsWithOptions(c.WelfareAchievement, h.GetCompanyTraitWelfareAchievements()),
		WelfarePopular:               shared_dto.ShowValueTextsWithOptions(c.WelfarePopular, h.GetCompanyTraitWelfarePopulars()),
		WelfareOther:                 shared_dto.ShowValueTextsWithOptions(c.WelfareOther, h.GetCompanyTraitWelfareOthers()),
		Other:                        shared_dto.ShowValuesTextWithOptions(c.Other, h.GetCompanyTraitOthers()),
		PR:                           c.PR,
		HPMCompanyDeclaration:        c.HPMCompanyDeclaration,
		IsHPMCertified:               c.IsHPMCertified(time.Now()),
		HPMCertificationDisplayYear:  c.HPMCertificationDisplayYear(),
		IsAgreedHatarakuhitoFirst:    c.IsAgreedHatarakuhitoFirst,
	}
}

// マッチしなかった場合、空文字を返すようにする
func showWebsite(str string) string {
	if softURLRegexp.MatchString(str) {
		return str
	}
	return ""
}

func showPrefecture(prefID master.PrefectureID, prefMap master.PrefectureMap) string {
	if p, found := prefMap.Get(prefID); found {
		return p.Name
	}
	return ""
}

func showAddress(a *company.Address, prefMap master.PrefectureMap) string {
	pName := showPrefecture(master.PrefectureID(a.PrefectureID), prefMap)
	return fmt.Sprintf("%s%s", pName, a.Address)
}

func showBusinessNames(bNames []string) []string {
	if len(bNames) > 1 { // 事業が複数ある場合は表示する、1件のみの場合は返さない
		return bNames
	}
	return []string{}
}

func showDocument(ds []*company.Document) []Document {
	view := make([]Document, 0, len(ds))
	for _, d := range ds {
		view = append(view, Document{
			ID:    d.ID,
			Label: d.Label,
		})
	}
	return view
}
