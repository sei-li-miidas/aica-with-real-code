package position

import (
	"context"
	"time"

	"github.com/samber/lo"

	pmodel "aica/api/api/mcptool/usecase/position/model"
	psupport "aica/api/api/mcptool/usecase/position/support"
	"aica/api/api/mcptool/usecase/shared_dto"
	"aica/api/domain/public/master"
	"aica/api/domain/user/apply/company"
	"aica/api/domain/user/apply/position"
	"aica/api/domain/user/domain_service/position_tag"
	userMaster "aica/api/domain/user/master"
	wposition "aica/api/domain/user/profile/will/position"
	"aica/api/sdk/aws/s3"
	merr "aica/api/sdk/error"
	"aica/api/sdk/logger"
	"aica/api/sdk/vo"
)

type detailPositionGetter interface {
	Get(id position.ID) (*position.Position, error)
}

type detailCompanyGetter interface {
	Get(id company.ID) (*company.Company, error)
}

type DetailUseCase struct {
	positionRepository detailPositionGetter
	companyRepository  detailCompanyGetter
	masterCache        *master.CacheProvider
	logger             logger.LevelLogger
}

func NewDetailUseCase(
	positionRepository detailPositionGetter,
	companyRepository detailCompanyGetter,
	masterCache *master.CacheProvider,
	l logger.LevelLogger,
) *DetailUseCase {
	return &DetailUseCase{
		positionRepository: positionRepository,
		companyRepository:  companyRepository,
		masterCache:        masterCache,
		logger:             l,
	}
}

type SharedInfo struct {
	Position *position.Position
	Company  *company.Company
}

// TODO: 外部公開しないように、レスポンスから各種ID（会社IDなど）を外す。
// Execute ポジション詳細情報取得
// JobChange, Regular, Spot, Commissionの4種対応。
func (uc *DetailUseCase) Execute(ctx context.Context, positionID position.ID) (*pmodel.PositionDetail, error) {
	i, err := uc.getSharedInfo(positionID)
	if err != nil {
		return nil, err
	}

	var (
		income *vo.FromTo
	)

	switch master.PositionEmploymentTypeID(lo.FromPtrOr(i.Position.GetEmploymentTypeID(), 0)) {
	case master.PositionEmploymentTypeIDEmployee, master.PositionEmploymentTypeIDContract:
		// 年収の下限はnilの場合があるが、上限は必ず設定される
		incomeFrom := 0
		if i.Position.GuaranteedIncome.BulkIncomeFrom != nil {
			incomeFrom = *i.Position.GuaranteedIncome.BulkIncomeFrom
		}
		income = &vo.FromTo{
			From: incomeFrom,
			To:   *i.Position.GuaranteedIncome.BulkIncomeTo,
		}
	case master.PositionEmploymentTypeIDOutsourcing, master.PositionEmploymentTypeIDSpotOutsourcing, master.PositionEmploymentTypeIDCommissionOutsourcing:
		break
	default:
		return nil, merr.ErrResourceNotFound.WithStack() // 「ポジションありません」的なエラーを表示するため
	}

	tags := position_tag.GetList(i.Position, i.Company)
	resCompany := buildDetailCompany(i.Company)
	resPosition := buildDetailPosition(i.Position, i.Company, income, tags, uc.masterCache)
	res := buildDetailResponse(resPosition, resCompany)
	return res, nil
}

func (uc *DetailUseCase) getSharedInfo(positionID position.ID) (*SharedInfo, error) {
	p, err := uc.positionRepository.Get(positionID)
	if err != nil {
		uc.logger.Error("failed to get position", "position_id", positionID, "error", err)
		return nil, merr.ErrInvalidRequest.WithStack()
	} else if p == nil {
		return nil, merr.ErrResourceNotFound.WithStack()
	}
	c, err := uc.companyRepository.Get(p.CompanyID)
	if err != nil {
		uc.logger.Error("failed to get company", "company_id", p.CompanyID, "error", err)
		return nil, merr.ErrInvalidRequest.WithStack()
	}

	return &SharedInfo{
		Position: p,
		Company:  c,
	}, nil
}

type OutsourcingFitting struct {
	IsMenkaku     bool
	IsInquiryable bool
}

type OutsourcingRegularFitting struct {
	IsMenkaku           bool
	IsInquiryable       bool
	TargetMatchRank     position.TargetMatchRank
	CompetencyMatchRank position.CompetencyMatchRank
	IsSatisfied         bool
}

func buildDetailCompany(c *company.Company) *pmodel.DetailCompany {
	return &pmodel.DetailCompany{
		Withdrawal:                  c.Withdrew,
		Name:                        c.Name,
		IsHPMCertified:              c.IsHPMCertified(time.Now()),
		HPMCertificationDisplayYear: c.HPMCertificationDisplayYear(),
		IsAgreedHatarakuhitoFirst:   c.IsAgreedHatarakuhitoFirst,
	}
}

func buildDetailPosition(
	p *position.Position,
	c *company.Company,
	income *vo.FromTo,
	tags []position.Tag,
	masterCache *master.CacheProvider,
) *pmodel.DetailPosition {
	if c.Withdrew { // 退会済みの場合、ポジション情報は表示しない
		return nil
	}
	// TODO: 呼び出し元（Agentサーバ）から渡してもらう。けど、希望勤務地はいまMCPサーバが持っている
	var willWorkaddress wposition.WorkAddress
	h := userMaster.TraitHelper{}
	return &pmodel.DetailPosition{
		ID:                                p.ID,
		CompanyID:                         p.CompanyID,
		CompanySectionID:                  p.CompanySectionID,
		BusinessID:                        p.BusinessID,
		IsDetailShowable:                  p.DetailShowableFlg,
		CompanyTrashedAt:                  p.TrashedAt,
		BossTypeScores:                    p.BossList,
		PublishStatus:                     p.GetPublishType(),
		Modified:                          p.LastModifiedAt,
		Title:                             p.Title,
		Post:                              shared_dto.ShowValueText(p.Post, h.GetPositionTraitPost),
		EmploymentType:                    shared_dto.ShowValueText(p.EmploymentType, h.GetPositionTraitEmploymentType),
		Images:                            showImages(p.Images),
		Jobs:                              psupport.ShowJobs(p.Jobs, masterCache),
		MainJobText:                       p.MainJobText,
		ModelAnnualIncome:                 psupport.ShowModelAnnualIncome(p.ModelAnnualIncome),
		StockOption:                       shared_dto.ShowValueText(p.StockOption, h.GetPositionTraitStockOption),
		BonusCount:                        shared_dto.ShowValueText(p.BonusCount, h.GetPositionTraitBonusCount),
		PromotionCount:                    shared_dto.ShowValueText(p.PromotionCount, h.GetPositionTraitPromotionCount),
		WorkAddress:                       psupport.ShowWorkAddresses(p.WorkAddress, willWorkaddress, masterCache),
		RemoteWork:                        psupport.ShowRemoteWork(p.RemoteWork, h.GetPositionTraitRemoteWork),
		RemoteWorkCondition:               p.RemoteWorkCondition,
		RemoteWorkOfficeFrequency:         shared_dto.ShowValueText(p.RemoteWorkOfficeFrequency, h.GetPositionTraitRemoteWorkOfficeFrequency),
		Holiday:                           shared_dto.ShowValueText(p.Holiday, h.GetPositionTraitHoliday),
		WorkTime:                          p.WorkTime,
		WorkTimeSystem:                    shared_dto.ShowValueText(p.WorkTimeSystem, h.GetPositionTraitWorkTimeSystem),
		WorkTimeNightsShift:               shared_dto.ShowValueText(p.WorkTimeNightsShift, h.GetPositionTraitWorkTimeNightsShift),
		OvertimeAvg:                       shared_dto.ShowValueText(p.OvertimeAvg, h.GetPositionTraitOvertimeAvg),
		OfficialTripFrequency:             shared_dto.ShowValueText(p.OfficialTripFrequency, h.GetPositionTraitOfficialTripFrequency),
		WorkEnvironment:                   shared_dto.ShowValueTexts(p.WorkingEnvironment, h.GetPositionTraitWorkingEnvironment),
		TransferenceExists:                shared_dto.ShowValueText(p.TransferenceExists, h.GetPositionTraitTransferenceExists),
		TransferenceFrequency:             shared_dto.ShowValueText(p.TransferenceFrequency, h.GetPositionTraitTransferenceFrequency),
		TransferenceAbroadExists:          shared_dto.ShowValueText(p.TransferenceAbroadExists, h.GetPositionTraitTransferenceAbroadExists),
		TransferenceAbroadEnglishIsUnused: shared_dto.ShowValueText(p.TransferenceAbroadEnglishIsUnused, h.GetPositionTraitTransferenceAbroadEnglishIsUnused),
		HREvaluationType:                  psupport.ShowHREvaluationType(p.HREvaluationType),
		HREvaluationCompetency:            psupport.ShowHREvaluationCompetency(p.HREvaluationCompetency),
		PR:                                p.PR,
		AccomplishmentImportance:          psupport.ShowValueTextWithOptions(p.AccomplishmentImportance, h.GetPositionTraitAccomplishmentImportances),
		AccomplishmentRate:                shared_dto.ShowValueText(p.AccomplishmentRate, h.GetPositionTraitAccomplishmentRate),
		SalesStyleDive:                    shared_dto.ShowValueText(p.SalesStyleDive, h.GetPositionTraitSalesStyleDive),
		SalesStyleTelAppointment:          shared_dto.ShowValueText(p.SalesStyleTelAppointment, h.GetPositionTraitSalesStyleTelAppointment),
		SalesStyleHost:                    shared_dto.ShowValueText(p.SalesStyleHost, h.GetPositionTraitSalesStyleHost),
		BaseMonthlySalary:                 psupport.ShowRawInputValueText(p.BaseMonthlySalary),
		OvertimeSalary:                    psupport.ShowOvertimeSalary(p.OvertimeSalary),
		CareerPathOutOfSiteExists:         shared_dto.ShowValueText(p.CareerPathOutOfSiteExists, h.GetPositionTraitCareerPathOutOfSiteExists),
		CareerPathWorkHeadOfficeExists:    shared_dto.ShowValueText(p.CareerPathWorkHeadOfficeExists, h.GetPositionTraitCareerPathWorkHeadOfficeExists),
		OrgTrendEngineerManagerExists:     shared_dto.ShowValueText(p.OrgTrendEngineerManagerExists, h.GetPositionTraitOrgTrendEngineerManagerExists),
		OrgTrendSectionMemberQty:          psupport.ShowRawInputValueText(p.OrgTrendSectionMemberQty),
		OrgTrendAccountingLicenceExists:   shared_dto.ShowValueText(p.OrgTrendAccountingLicenceExists, h.GetPositionTraitOrgTrendAccountingLicenceExists),
		OrgTrendLegalLicenceExists:        shared_dto.ShowValueText(p.OrgTrendLegalLicenceExists, h.GetPositionTraitOrgTrendLegalLicenceExists),
		OrgTrendRelatedWithEngineer:       shared_dto.ShowValueText(p.OrgTrendRelatedWithEngineer, h.GetPositionTraitOrgTrendRelatedWithEngineer),
		ITEngineerWorkEnvironment:         shared_dto.ShowValuesText(p.WorkEnvironment, h.GetPositionTraitWorkEnvironment),
		DevelopmentTerm:                   shared_dto.ShowValueText(p.DevelopmentTerm, h.GetPositionTraitDevelopmentTerm),
		DevelopmentProcess:                psupport.ShowValueTextWithOptions(p.DevelopmentProcess, h.GetPositionTraitDevelopmentProcesses),
		EmergencySupport:                  shared_dto.ShowValueText(p.EmergencySupport, h.GetPositionTraitEmergencySupport),
		JoinedReserve:                     p.JoinedReserve,
		EmploymentToRegularEmployee:       shared_dto.ShowValueText(p.EmploymentToRegularEmployee, h.GetPositionTraitEmploymentToRegularEmployee),
		Probation:                         shared_dto.ShowValueText(p.Probation, h.GetPositionTraitProbation),
		ContractPeriod:                    shared_dto.ShowValueText(p.ContractPeriod, h.GetPositionTraitContractPeriod),
		ContractRenewal:                   shared_dto.ShowValueText(p.ContractRenewal, h.GetPositionTraitContractRenewal),
		ContractRenewalText:               p.ContractRenewalText,
		ContractExtension:                 shared_dto.ShowValueText(p.ContractExtension, h.GetPositionTraitContractExtension),
		JobChange:                         psupport.ShowJobChange(income, p.GuaranteedIncome),
		RegularOutsourcing:                psupport.ShowRegularOutsourcing(p.RegularOutsourcing),
		SpotOutsourcing:                   psupport.ShowSpotOutsourcing(p.SpotOutsourcing),
		SpotJobRequest:                    psupport.ShowSpotJobRequest(p, masterCache.SpotJobRequestMap()),
		SpotJobDescription:                p.SpotJobDescription,
		SpotExpLevels:                     psupport.ShowSpotExpLevels(p, masterCache.SpotJobRequestMap(), masterCache.SpotExpLevels().GetByPattern),
		CommissionOutsourcing:             psupport.ShowCommissionOutsourcing(p.CommissionFeeCondition, p.CommissionBusinessDescription),
		EmploymentTypeChange:              shared_dto.ShowValueText(p.EmploymentTypeChange, h.GetPositionTraitEmploymentTypeChange),
		OutsourcingAppeal:                 psupport.ShowOutsourcingAppeal(p),
		SmokeFree:                         shared_dto.ShowValueText(p.SmokeFree, h.GetPositionTraitSmokeFree),
		SmokeFreeEnvironment:              shared_dto.ShowValueText(p.SmokeFreeEnvironment, h.GetPositionTraitSmokeFreeEnvironment),
		Tags:                              tags,
		Interview:                         psupport.ShowInterview(p.IsSpot(), &p.Interview, masterCache),
	}
}

func showImages(images position.Images) []*pmodel.Image {
	if len(images) == 0 {
		return nil
	}
	endpoint, err := s3.GetUserEndpoint()
	if err != nil {
		return nil
	}

	ret := make([]*pmodel.Image, 0, len(images))
	for _, i := range images {

		ret = append(ret, &pmodel.Image{
			DisplayType: i.DisplayType,
			URL:         endpoint.JoinPath(i.FilePath).String(),
		})
	}
	return ret
}

func buildDetailResponse(
	p *pmodel.DetailPosition,
	c *pmodel.DetailCompany,
) *pmodel.PositionDetail {
	r := &pmodel.PositionDetail{
		Position: p,
		Company:  c,
	}
	return r
}
