package business

import (
	"github.com/pkg/errors"
	"github.com/samber/lo"

	"aica/api/api/mcptool/usecase/shared_dto"
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/business"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
	applyVO "aica/api/domain/user/apply/vo"
	userMaster "aica/api/domain/user/master"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"aica/api/sdk/vo"
)

type GetDetailUseCase struct {
	logger           logger.LevelLogger
	readPositionRepo readPositionRepository
	readBusinessRepo readBusinessRepository
	readCompanyRepo  readCompanyRepository
	industryMaster   industrySmallNameProvider
}

func NewGetDetailUseCaseWithRepositories(
	l logger.LevelLogger,
	readPositionRepo readPositionRepository,
	readBusinessRepo readBusinessRepository,
	readCompanyRepo readCompanyRepository,
	industryMaster industrySmallNameProvider,
) *GetDetailUseCase {
	return &GetDetailUseCase{
		logger:           l,
		readPositionRepo: readPositionRepo,
		readBusinessRepo: readBusinessRepo,
		readCompanyRepo:  readCompanyRepo,
		industryMaster:   industryMaster,
	}
}

type GetDetailResponse struct {
	Business Detail
}

type Detail struct {
	ID        business.ID
	CompanyID company.ID
	Name      string

	EmployeeQty                    *shared_dto.ValueText
	EstablishmentYear              *shared_dto.ValueText
	SalesScale                     *shared_dto.ValueText
	Industries                     *industries
	Stage                          *shared_dto.ValueText
	Product                        *product
	TargetCustomer                 *targetCustomer
	TrendKeyword                   *shared_dto.ValuesText
	MarketProspect                 *shared_dto.ValueText
	Strategy                       *shared_dto.ValueText
	Advantage                      *shared_dto.ValueText
	DecisionType                   *decisionType
	EmployeeAverageAge             *shared_dto.ValueText
	EmployeeWomanRate              *shared_dto.ValueText
	EmployeeMidCareerRate          *shared_dto.ValueText
	EmployeeForeignNationalityRate *shared_dto.ValueText
	EmployeeCharacter              *employeeCharacter
	HREvaluationPromotionSpeed     *shared_dto.ValueText
	ForeignNationalityRecruiting   *bool

	// 以下、業種によって有無が決定される
	MedicalAdvantageField         *shared_dto.ValuesTextWithOptions
	CarPartsTier                  *shared_dto.ValueTextWithOptions
	SIType                        *shared_dto.ValueTextWithOptions
	SIAdvantageIndustry           *shared_dto.ValuesTextWithOptions
	ContractCompanyProfitSource   *shared_dto.ValueTextWithOptions
	ContractCompanyProjectTerm    *shared_dto.ValueTextWithOptions
	ContractCompanyClientResident *shared_dto.ValueTextWithOptions
	ContractCompanyResident       *shared_dto.ValueTextWithOptions
}

type (
	industries struct {
		Industries []industry
		Note       string
	}

	industry struct {
		SmallID master.IndustrySmallID
		Name    string
		IsMain  bool
	}
)

type (
	product struct {
		Share          *shared_dto.ValueText
		HasOwnProducts *shared_dto.FlagText
		Tangibleness   *tangibleness
	}

	tangibleness struct {
		Tangible   *shared_dto.Flag
		Intangible *shared_dto.Flag
		Note       string
	}
)

type (
	targetCustomer struct {
		BtoBExists *bool
		BtoCExists *bool
		Note       string
		BtoB       *bToB
		BtoC       *bToC
	}

	bToB struct {
		IndustrySmalls []*vo.IDNamePair[int]
		Note           string
	}

	bToC struct {
		Targets []*vo.IDNamePair[int]
		Note    string
	}
)

type decisionType struct {
	Type1 *vo.IDNamePair[int]
	Type2 *vo.IDNamePair[int]
	Type3 *vo.IDNamePair[int]
	Type4 *vo.IDNamePair[int]
	Note  string
}

type employeeCharacter struct {
	Character1  *vo.IDNamePair[int]
	Character2  *vo.IDNamePair[int]
	Character3  *vo.IDNamePair[int]
	Character4  *vo.IDNamePair[int]
	Character5  *vo.IDNamePair[int]
	Character6  *vo.IDNamePair[int]
	Character7  *vo.IDNamePair[int]
	Character8  *vo.IDNamePair[int]
	Character9  *vo.IDNamePair[int]
	Character10 *vo.IDNamePair[int]
	Character11 *vo.IDNamePair[int]
	Character12 *vo.IDNamePair[int]
	Note        string
}

// TODO: 外部公開しないように、レスポンスから各種ID（会社IDなど）を外す。
func (uc *GetDetailUseCase) Execute(positionID position.ID) (*GetDetailResponse, error) {
	businessID, err := uc.readPositionRepo.GetBusinessID(positionID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(errors.WithMessage(err, "事業の取得処理に失敗しました"))
	} else if businessID == nil {
		return nil, merr.ErrResourceNotFound.WithStack()
	}

	b, err := uc.readBusinessRepo.Get(*businessID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(errors.WithMessage(err, "事業の取得処理に失敗しました"))
	}
	if b == nil {
		return nil, merr.ErrResourceNotFound.WithStack()
	}
	// 事業が削除済み(trashed)の場合でも、ユーザーが応募済みときは見えてほしいのでエラーにしない
	// 応募してない場合でも削除済み(trashed)のものが見えてしまう可能性があるが、基本は導線がないはずなので許容とする

	c, err := uc.readCompanyRepo.Get(b.CompanyID)
	if err != nil {
		return nil, merr.ErrInternalServer.WithCause(errors.WithMessage(err, "企業の取得処理に失敗しました"))
	}
	if c == nil {
		uc.logger.Error("データ不整合: 事業に紐づく企業が存在しません", "businessID", businessID, "companyID", b.CompanyID)
		return nil, merr.ErrInternalServer.WithStack()
	}
	if !c.IsRegistered() {
		return nil, merr.ErrResourceNotFound.WithStack()
	}

	return buildGetDetailResponse(b, uc.industryMaster.GetIndustrySmallNameIncludingAllIndustry), nil
}

func buildGetDetailResponse(
	b *business.Business,
	resolveIndustrySmallName func(smallID master.IndustrySmallID) string,
) *GetDetailResponse {
	h := userMaster.TraitHelper{}
	return &GetDetailResponse{
		Business: Detail{
			ID:                             b.ID,
			CompanyID:                      b.CompanyID,
			Name:                           b.Name,
			EmployeeQty:                    shared_dto.ShowValueText(b.EmployeeQty, h.GetBusinessTraitEmployeeQty),
			Industries:                     showIndustries(b.Industries),
			EstablishmentYear:              shared_dto.ShowValueText(b.EstablishmentYear, h.GetBusinessTraitYearsOfEstablishment),
			SalesScale:                     shared_dto.ShowValueText(b.SalesScale, h.GetBusinessTraitSalesScale),
			Stage:                          shared_dto.ShowValueText(b.Stage, h.GetBusinessTraitBusinessStage),
			Product:                        showProduct(h, b.Product),
			TargetCustomer:                 showTargetCustomer(h, b.TargetCustomer, resolveIndustrySmallName),
			TrendKeyword:                   shared_dto.ShowValuesText(b.TrendKeyword, h.GetBusinessTraitTrendKeyword),
			MarketProspect:                 shared_dto.ShowValueText(b.MarketProspect, h.GetBusinessTraitMarketProspect),
			Strategy:                       shared_dto.ShowValueText(b.Strategy, h.GetBusinessTraitBusinessStrategy),
			Advantage:                      shared_dto.ShowValueText(b.Advantage, h.GetBusinessTraitAdvantage),
			DecisionType:                   showDecisionType(h, b.DecisionType),
			EmployeeAverageAge:             shared_dto.ShowValueText(b.EmployeeAverageAge, h.GetBusinessTraitEmployeeAverageAge),
			EmployeeWomanRate:              shared_dto.ShowValueText(b.EmployeeWomanRate, h.GetBusinessTraitEmployeeWomanRate),
			EmployeeMidCareerRate:          shared_dto.ShowValueText(b.EmployeeMidCareerRate, h.GetBusinessTraitEmployeeMidCareerRate),
			EmployeeForeignNationalityRate: shared_dto.ShowValueText(b.EmployeeForeignNationalityRate, h.GetBusinessTraitEmployeeForeignNationalityRate),
			EmployeeCharacter:              showEmployeeCharacter(h, b.EmployeeCharacter),
			HREvaluationPromotionSpeed:     shared_dto.ShowValueText(b.HREvaluationPromotionSpeed, h.GetBusinessTraitHREvaluationPromotionSpeed),
			ForeignNationalityRecruiting:   b.ForeignNationalityRecruiting,
			MedicalAdvantageField:          shared_dto.ShowValuesTextWithOptions(b.MedicalAdvantageField, h.GetBusinessTraitMedicalAdvantageFieldAll()),
			CarPartsTier:                   shared_dto.ShowValueTextWithOptions(b.CarPartsTier, h.GetBusinessTraitCarPartsTierAll()),
			SIType:                         shared_dto.ShowValueTextWithOptions(b.SIType, h.GetBusinessTraitSITypeAll()),
			SIAdvantageIndustry:            shared_dto.ShowValuesTextWithOptions(b.SIAdvantageIndustry, h.GetBusinessTraitSIAdvantageIndustryAll()),
			ContractCompanyProfitSource:    shared_dto.ShowValueTextWithOptions(b.ContractCompanyProfitSource, h.GetBusinessTraitContractCompanyProfitSourceAll()),
			ContractCompanyProjectTerm:     shared_dto.ShowValueTextWithOptions(b.ContractCompanyProjectTerm, h.GetBusinessTraitContractCompanyProjectTermAll()),
			ContractCompanyClientResident:  shared_dto.ShowValueTextWithOptions(b.ContractCompanyClientResident, h.GetBusinessTraitContractCompanyClientResidentAll()),
			ContractCompanyResident:        shared_dto.ShowValueTextWithOptions(b.ContractCompanyResident, h.GetBusinessTraitContractCompanyResidentTypeAll()),
		},
	}
}

func showIndustries(src *business.Industries) *industries {
	if src == nil {
		return nil
	}

	var tgtIndustries []industry
	if src.Industries != nil {
		tgtIndustries = make([]industry, 0, len(src.Industries))
		for _, s := range src.Industries {
			tgtIndustries = append(tgtIndustries, industry{
				SmallID: s.SmallID,
				Name:    s.Label,
				IsMain:  s.MainFlg,
			})
		}
	}

	return &industries{
		Industries: tgtIndustries,
		Note:       lo.FromPtrOr(src.Text, ""),
	}
}

func showProduct(h userMaster.TraitHelper, src *business.Product) *product {
	if src == nil {
		return nil
	}

	return &product{
		Share:          shared_dto.ShowValueText(src.Share, h.GetBusinessTraitProductShare),
		HasOwnProducts: shared_dto.ShowFlagText(src.HasOwnProducts, h.GetBusinessTraitHasOwnProducts),
		Tangibleness:   showTangibleness(h, src.Tangibleness),
	}
}

func showTangibleness(h userMaster.TraitHelper, src *business.Tangibleness) *tangibleness {
	if src == nil {
		return nil
	}

	return &tangibleness{
		Tangible:   shared_dto.ShowFlagWithFlagName(src.Tangible, h.GetBusinessTraitProductsTangible()),
		Intangible: shared_dto.ShowFlagWithFlagName(src.Intangible, h.GetBusinessTraitProductsIntangible()),
		Note:       lo.FromPtrOr(src.Text, ""),
	}
}

func showTargetCustomer(h userMaster.TraitHelper, src *business.TargetCustomer, resolveIndustrySmallName func(smallID master.IndustrySmallID) string) *targetCustomer {
	if src == nil {
		return nil
	}

	return &targetCustomer{
		BtoBExists: src.BtoBExists,
		BtoCExists: src.BtoCExists,
		BtoB:       showBtoB(src.BtoB, resolveIndustrySmallName),
		BtoC:       showBtoC(h, src.BtoC),
		Note:       lo.FromPtrOr(src.Text, ""),
	}
}

func showBtoB(src *business.BtoB, resolveIndustrySmallName func(smallID master.IndustrySmallID) string) *bToB {
	if src == nil {
		return nil
	}

	return &bToB{
		IndustrySmalls: showBtoBIndustrySmalls(src.IndustrySmallIDs, resolveIndustrySmallName),
		Note:           lo.FromPtrOr(src.Text, ""),
	}
}

func showBtoBIndustrySmalls(src applyVO.IDOnlyList, resolveIndustrySmallName func(smallID master.IndustrySmallID) string) []*vo.IDNamePair[int] {
	if src == nil {
		return nil
	}

	tgt := make([]*vo.IDNamePair[int], 0, len(src))
	for _, s := range src {
		smallID := master.IndustrySmallID(s.ID)
		name := resolveIndustrySmallName(smallID)
		tgt = append(tgt, vo.NewIDNamePair(s.ID, name))
	}

	return tgt
}

func showBtoC(h userMaster.TraitHelper, src *business.BtoC) *bToC {
	if src == nil {
		return nil
	}

	return &bToC{
		Targets: showBtoCTargets(h, src.TargetIDs),
		Note:    lo.FromPtrOr(src.Text, ""),
	}
}

func showBtoCTargets(h userMaster.TraitHelper, src applyVO.IDOnlyList) []*vo.IDNamePair[int] {
	if src == nil {
		return nil
	}

	options := h.GetBusinessTraitTargetCustomer2CAll()

	tgt := make([]*vo.IDNamePair[int], 0, len(src))
	for _, s := range src {
		tgt = append(tgt, vo.NewIDNamePair(s.ID, options.Get(s.ID).GetUserSideName()))
	}

	return tgt
}

func showDecisionType(h userMaster.TraitHelper, src *business.DecisionType) *decisionType {
	if src == nil {
		return nil
	}

	options := h.GetBusinessTraitDecisionTypeAll()

	return &decisionType{
		Type1: showDecisionTypeValue(options, src.Type1),
		Type2: showDecisionTypeValue(options, src.Type2),
		Type3: showDecisionTypeValue(options, src.Type3),
		Type4: showDecisionTypeValue(options, src.Type4),
		Note:  src.Text,
	}
}

func showDecisionTypeValue(options master.TraitBusinessOptionListForUser, v int) *vo.IDNamePair[int] {
	if v == 0 { // 未選択
		return nil
	}

	return vo.NewIDNamePair(v, options.Get(v).GetUserSideName())
}

func showEmployeeCharacter(h userMaster.TraitHelper, src *business.EmployeeCharacter) *employeeCharacter {
	if src == nil {
		return nil
	}

	options := h.GetBusinessTraitEmployeeCharacterAll()

	return &employeeCharacter{
		Character1:  showEmployeeCharacterValue(options, src.Character1),
		Character2:  showEmployeeCharacterValue(options, src.Character2),
		Character3:  showEmployeeCharacterValue(options, src.Character3),
		Character4:  showEmployeeCharacterValue(options, src.Character4),
		Character5:  showEmployeeCharacterValue(options, src.Character5),
		Character6:  showEmployeeCharacterValue(options, src.Character6),
		Character7:  showEmployeeCharacterValue(options, src.Character7),
		Character8:  showEmployeeCharacterValue(options, src.Character8),
		Character9:  showEmployeeCharacterValue(options, src.Character9),
		Character10: showEmployeeCharacterValue(options, src.Character10),
		Character11: showEmployeeCharacterValue(options, src.Character11),
		Character12: showEmployeeCharacterValue(options, src.Character12),
		Note:        src.Text,
	}
}

func showEmployeeCharacterValue(options master.TraitBusinessOptionListForUser, v int) *vo.IDNamePair[int] {
	if v == 0 { // 未選択
		return nil
	}

	return vo.NewIDNamePair(v, options.Get(v).GetUserSideName())
}
