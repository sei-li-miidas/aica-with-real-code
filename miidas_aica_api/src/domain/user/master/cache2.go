package master

import (
	"aica/api/domain/public/master"
)

// TraitHelper トレイトを簡便に扱うためのヘルパー
type TraitHelper struct {
}

// GetBusinessTraitEmployeeQty 事業概要_事業の従業員数
func (h TraitHelper) GetBusinessTraitEmployeeQty(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxEmployeeQty).Get(id).GetUserSideName()
}

// GetBusinessTraitYearsOfEstablishment 事業概要_事業の設立
func (h TraitHelper) GetBusinessTraitYearsOfEstablishment(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxYearsOfEstablishment).Get(id).GetUserSideName()
}

// GetBusinessTraitSalesScale 事業概要_事業の売上規模
func (h TraitHelper) GetBusinessTraitSalesScale(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxSalesScale).Get(id).GetUserSideName()
}

// GetBusinessTraitBusinessStage 事業概要_事業ステータス
func (h TraitHelper) GetBusinessTraitBusinessStage(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxBusinessStage).Get(id).GetUserSideName()
}

// GetBusinessTraitProductShare 事業概要_商材・サービスの特徴_ポジション
func (h TraitHelper) GetBusinessTraitProductShare(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxProductsShare).Get(id).GetUserSideName()
}

// GetBusinessTraitHasOwnProducts 事業概要_商材・サービスの特徴_本事業の商材・サービス
func (h TraitHelper) GetBusinessTraitHasOwnProducts(on bool) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxHasOwnProducts).GetByBool(on).GetUserSideName()
}

// GetBusinessTraitProductsTangible 事業概要_商材・サービスの特徴_有形無形_有形
func (h TraitHelper) GetBusinessTraitProductsTangible() string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxProductsTangibleness).Get(master.Tangible).GetUserSideName()
}

// GetBusinessTraitProductsIntangible 事業概要_商材・サービスの特徴_有形無形_無形
func (h TraitHelper) GetBusinessTraitProductsIntangible() string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxProductsTangibleness).Get(master.Intangible).GetUserSideName()
}

// GetBusinessTraitTargetCustomer2CAll 事業概要_対象顧客_BtoC
func (h TraitHelper) GetBusinessTraitTargetCustomer2CAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxTargetCustomer2C)
}

// GetBusinessTraitTrendKeyword 事業概要_トレンドキーワード
func (h TraitHelper) GetBusinessTraitTrendKeyword(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxTrendKeyword).Get(id).GetUserSideName()
}

// GetBusinessTraitMarketProspect 事業概要_マーケット
func (h TraitHelper) GetBusinessTraitMarketProspect(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxMarketProspect).Get(id).GetUserSideName()
}

// GetBusinessTraitBusinessStrategy 事業概要_戦略
func (h TraitHelper) GetBusinessTraitBusinessStrategy(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxBusinessStrategy).Get(id).GetUserSideName()
}

// GetBusinessTraitAdvantage 事業概要_事業の強み
func (h TraitHelper) GetBusinessTraitAdvantage(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxAdvantage).Get(id).GetUserSideName()
}

// GetBusinessTraitDecisionTypeAll 事業概要_意思決定と裁量
func (h TraitHelper) GetBusinessTraitDecisionTypeAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxDecisionType)
}

// GetBusinessTraitEmployeeAverageAge 社員属性_平均年齢
func (h TraitHelper) GetBusinessTraitEmployeeAverageAge(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxEmployeeAverageAge).Get(id).GetUserSideName()
}

// GetBusinessTraitEmployeeWomanRate 社員属性_女性社員比率
func (h TraitHelper) GetBusinessTraitEmployeeWomanRate(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxEmployeeWomanRate).Get(id).GetUserSideName()
}

// GetBusinessTraitEmployeeMidCareerRate 社員属性_中途入社社員比率
func (h TraitHelper) GetBusinessTraitEmployeeMidCareerRate(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxEmployeeMidCareerRate).Get(id).GetUserSideName()
}

// GetBusinessTraitEmployeeForeignNationalityRate 社員属性_外国籍社員比率
func (h TraitHelper) GetBusinessTraitEmployeeForeignNationalityRate(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxEmployeeForeignNationalityRate).Get(id).GetUserSideName()
}

// GetBusinessTraitEmployeeCharacterAll 社員属性_組織・社員の特徴
func (h TraitHelper) GetBusinessTraitEmployeeCharacterAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxEmployeeCharacter)
}

// GetBusinessTraitHREvaluationPromotionSpeed 人事評価_昇進昇格スピード
func (h TraitHelper) GetBusinessTraitHREvaluationPromotionSpeed(id int) string {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtxHREvaluationPromotionSpeed).Get(id).GetUserSideName()
}

// GetBusinessTraitMedicalAdvantageField 業種別事業特徴_メディカル系_得意領域（メディカル）
func (h TraitHelper) GetBusinessTraitMedicalAdvantageFieldAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiMedicalAdvantageField)
}

// GetBusinessTraitCarPartsTier 業種別事業特徴_メーカー（自動車部品）_Tier
func (h TraitHelper) GetBusinessTraitCarPartsTierAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiCarPartsTier)
}

// GetBusinessTraitSIType 業種別事業特徴_システムインテグレーター_Si種別
func (h TraitHelper) GetBusinessTraitSITypeAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiSIType)
}

// GetBusinessTraitSIAdvantageIndustry 業種別事業特徴_システムインテグレーター_得意領域（Sire）
func (h TraitHelper) GetBusinessTraitSIAdvantageIndustryAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiSIAdvantageIndustry)
}

// GetBusinessTraitContractCompanyProfitSource 業種別事業特徴_請負会社の特徴_主な収益源_システムインテグレーター_Si種別
func (h TraitHelper) GetBusinessTraitContractCompanyProfitSourceAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiContractCompanyProfitSource)
}

// GetBusinessTraitContractCompanyProjectTerm 業種別事業特徴_請負会社の特徴_プロジェクト期間
func (h TraitHelper) GetBusinessTraitContractCompanyProjectTermAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiContractCompanyProjectTerm)
}

// GetBusinessTraitContractCompanyClientResident 業種別事業特徴_請負会社の特徴_客先常駐
func (h TraitHelper) GetBusinessTraitContractCompanyClientResidentAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiContractCompanyClientResident)
}

// GetBusinessTraitContractCompanyResidentType 業種別事業特徴_請負会社の特徴_常駐形態
func (h TraitHelper) GetBusinessTraitContractCompanyResidentTypeAll() master.TraitBusinessOptionListForUser {
	return master.Provider().GetTraitBusinessOptionsForUser(master.BtiContractCompanyResidentType)
}

// GetCompanyTraitProfitCompany 企業概要_法人種別
func (h TraitHelper) GetCompanyTraitProfitCompany(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxIsProfitCompany).Get(id).GetUserSideName()
}

// GetCompanyTraitEmployeeQty 企業概要_従業員数
func (h TraitHelper) GetCompanyTraitEmployeeQty(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxEmployeeQty).Get(id).GetUserSideName()
}

// GetCompanyTraitEstablishmentYear 企業概要_設立
func (h TraitHelper) GetCompanyTraitEstablishmentYear(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxYearsOfEstablishment).Get(id).GetUserSideName()
}

// GetCompanyTraitSalesScale 企業概要_売上規模
func (h TraitHelper) GetCompanyTraitSalesScale(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxSalesScale).Get(id).GetUserSideName()
}

// GetCompanyTraitSalesOverseasRate 事業概要_海外売上比率
func (h TraitHelper) GetCompanyTraitSalesOverseasRate(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxSalesOverseasRate).Get(id).GetUserSideName()
}

// GetCompanyTraitEmployeeWorkAbroadRate 社員属性_海外駐在社員比率
func (h TraitHelper) GetCompanyTraitEmployeeWorkAbroadRate(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxEmployeeWorkAbroadRate).Get(id).GetUserSideName()
}

// GetCompanyTraitYearHolidays 休日休暇_年間休日
func (h TraitHelper) GetCompanyTraitYearHolidays(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxYearHolidays).Get(id).GetUserSideName()
}

// GetCompanyTraitSideBusiness 副業
func (h TraitHelper) GetCompanyTraitSideBusiness(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxSideBusiness).Get(id).GetUserSideName()
}

// GetCompanyTraitPaidHolidayUseRate 休日休暇_有給休暇取得率
func (h TraitHelper) GetCompanyTraitPaidHolidayUseRate(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxPaidHolidayUseRate).Get(id).GetUserSideName()
}

// GetCompanyTraitJobRotationExists キャリア_ジョブローテーション
func (h TraitHelper) GetCompanyTraitJobRotationExists(on bool) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxJobRotationExists).GetByBool(on).GetUserSideName()
}

// GetCompanyTraitChangeDepartmentRequest キャリア_異動希望申請制度
func (h TraitHelper) GetCompanyTraitChangeDepartmentRequest(on bool) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxChangeDepartmentRequest).GetByBool(on).GetUserSideName()
}

// GetCompanyTraitSpecialistCareerPath キャリア_スペシャリストキャリアパス
func (h TraitHelper) GetCompanyTraitSpecialistCareerPath(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxSpecialistCareerPath).Get(id).GetUserSideName()
}

// GetCompanyTraitHREvaluationWomanManagerRate 人事評価_人事評価実績_女性管理職比率
func (h TraitHelper) GetCompanyTraitHREvaluationWomanManagerRate(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxHREvaluationWomanManagerRate).Get(id).GetUserSideName()
}

// GetCompanyTraitHREvaluation20sManagerRate 人事評価_人事評価実績_20代管理職
func (h TraitHelper) GetCompanyTraitHREvaluation20sManagerRate(id int) string {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxHREvaluation20SManagerRate).Get(id).GetUserSideName()
}

// GetCompanyTraitCapitalTypes 企業概要_資本区分 全項目
func (h TraitHelper) GetCompanyTraitCapitalTypes() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxCapitalType)
}

// GetCompanyTraitAppealPoints 企業概要_当社のアピールポイント 全項目
func (h TraitHelper) GetCompanyTraitAppealPoints() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxAppealPoint)
}

// GetCompanyTraitWelfareBenefits 待遇_福利厚生（待遇編） 全項目
func (h TraitHelper) GetCompanyTraitWelfareBenefits() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxWelfareBenefit)
}

// GetCompanyTraitWelfareInsurances 福利厚生_社会保険 全項目
func (h TraitHelper) GetCompanyTraitWelfareInsurances() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxWelfareInsurance)
}

// GetCompanyTraitVacationsAll 休日休暇_福利厚生（休日休暇編） 全項目
func (h TraitHelper) GetCompanyTraitVacationsAll() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxVacations)
}

// GetCompanyTraitHREvaluationSpecialSystems 人事評価_特殊な評価制度 全項目
func (h TraitHelper) GetCompanyTraitHREvaluationSpecialSystems() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxHREvaluationSpecialSystem)
}

// GetCompanyTraitWelfareAchievements 福利厚生_実績のある福利厚生 全項目
func (h TraitHelper) GetCompanyTraitWelfareAchievements() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxWelfareAchievement)
}

// GetCompanyTraitWelfarePopulars 福利厚生_人気の福利厚生 全項目
func (h TraitHelper) GetCompanyTraitWelfarePopulars() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxWelfarePopular)
}

// GetCompanyTraitWelfareOthers 福利厚生_その他福利厚生 項目
func (h TraitHelper) GetCompanyTraitWelfareOthers() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxWelfareOther)
}

// GetCompanyTraitOthers その他企業特徴 全項目
func (h TraitHelper) GetCompanyTraitOthers() master.TraitCompanyOptionListForUser {
	return master.Provider().GetTraitCompanyOptionsForUser(master.CtxOther)
}

// GetPositionTraitPost 役職
func (h TraitHelper) GetPositionTraitPost(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxPost).Get(id).GetUserSideName()
}

// GetPositionTraitEmploymentType 契約形態種別
func (h TraitHelper) GetPositionTraitEmploymentType(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxEmploymentType).Get(id).GetUserSideName()
}

// GetPositionTraitStockOption 待遇_ストックオプション
func (h TraitHelper) GetPositionTraitStockOption(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxStockOption).Get(id).GetUserSideName()
}

// GetPositionTraitBonusCount 待遇_賞与
func (h TraitHelper) GetPositionTraitBonusCount(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxBonusCount).Get(id).GetUserSideName()
}

// GetPositionTraitPromotionCount 待遇_昇給・昇格
func (h TraitHelper) GetPositionTraitPromotionCount(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxPromotionCount).Get(id).GetUserSideName()
}

// GetPositionTraitRemoteWork リモート勤務
func (h TraitHelper) GetPositionTraitRemoteWork(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxRemoteWork).Get(id).GetUserSideName()
}

// GetPositionTraitRemoteWorkOfficeFrequency リモート勤務_出社頻度
func (h TraitHelper) GetPositionTraitRemoteWorkOfficeFrequency(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxRemoteWorkOfficeFrequency).Get(id).GetUserSideName()
}

// GetPositionTraitHoliday 休日
func (h TraitHelper) GetPositionTraitHoliday(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxHoliday).Get(id).GetUserSideName()
}

// GetPositionTraitWorkTimeSystem 勤務時間
func (h TraitHelper) GetPositionTraitWorkTimeSystem(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxWorkTime).Get(id).GetUserSideName()
}

// GetPositionTraitWorkTimeNightsShift 勤務時間_夜勤の有無
func (h TraitHelper) GetPositionTraitWorkTimeNightsShift(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxWorkTimeNightShift).Get(id).GetUserSideName()
}

// GetPositionTraitOvertimeAvg 労働環境_平均残業時間
func (h TraitHelper) GetPositionTraitOvertimeAvg(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxOvertimeAvg).Get(id).GetUserSideName()
}

// GetPositionTraitOfficialTripFrequency 労働環境_出張頻度
func (h TraitHelper) GetPositionTraitOfficialTripFrequency(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxOfficialTripFrequency).Get(id).GetUserSideName()
}

// GetPositionTraitWorkingEnvironment 労働環境_労働環境の特徴
func (h TraitHelper) GetPositionTraitWorkingEnvironment(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxWorkingEnvironment).Get(id).GetUserSideName()
}

// GetPositionTraitTransferenceExists キャリア_国内転勤の有無
func (h TraitHelper) GetPositionTraitTransferenceExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxTransferenceExists).Get(id).GetUserSideName()
}

// GetPositionTraitTransferenceFrequency キャリア_国内転勤の有無_国内転勤の頻度
func (h TraitHelper) GetPositionTraitTransferenceFrequency(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxTransferenceFrequency).Get(id).GetUserSideName()
}

// GetPositionTraitTransferenceAbroadExists キャリア_海外転勤
func (h TraitHelper) GetPositionTraitTransferenceAbroadExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxTransferenceAbroadExists).Get(id).GetUserSideName()
}

// GetPositionTraitTransferenceAbroadEnglishIsUnused キャリア_海外転勤_英語力不問
func (h TraitHelper) GetPositionTraitTransferenceAbroadEnglishIsUnused(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxTransferenceAbroadEnglishIsUnused).Get(id).GetUserSideName()
}

// GetPositionTraitAccomplishmentRate ポジション特徴_業績目標達成者率
func (h TraitHelper) GetPositionTraitAccomplishmentRate(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjAccomplishmentRate).Get(id).GetUserSideName()
}

// GetPositionTraitSalesStyleDive ポジション特徴_営業スタイル_新規飛び込み
func (h TraitHelper) GetPositionTraitSalesStyleDive(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjSalesStyleDive).Get(id).GetUserSideName()
}

// GetPositionTraitSalesStyleTelAppointment ポジション特徴_営業スタイル_新規テレアポ
func (h TraitHelper) GetPositionTraitSalesStyleTelAppointment(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjSalesStyleTelAppointment).Get(id).GetUserSideName()
}

// GetPositionTraitSalesStyleHost ポジション特徴_営業スタイル_接待
func (h TraitHelper) GetPositionTraitSalesStyleHost(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjSalesStyleHost).Get(id).GetUserSideName()
}

// GetPositionTraitCareerPathOutOfSiteExists ポジション特徴_キャリアパス_1
func (h TraitHelper) GetPositionTraitCareerPathOutOfSiteExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjCareerPathOutOfSiteExists).Get(id).GetUserSideName()
}

// GetPositionTraitCareerPathWorkHeadOfficeExists ポジション特徴_キャリアパス_2
func (h TraitHelper) GetPositionTraitCareerPathWorkHeadOfficeExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjCareerPathWorkHeadOfficeExists).Get(id).GetUserSideName()
}

// GetPositionTraitOrgTrendEngineerManagerExists ポジション特徴_組織_1
func (h TraitHelper) GetPositionTraitOrgTrendEngineerManagerExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjOrgTrendEngineerManagerExists).Get(id).GetUserSideName()
}

// GetPositionTraitOrgTrendAccountingLicenceExists ポジション特徴_組織_3
func (h TraitHelper) GetPositionTraitOrgTrendAccountingLicenceExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjOrgTrendAccountingLicenceExists).Get(id).GetUserSideName()
}

// GetPositionTraitOrgTrendLegalLicenceExists ポジション特徴_組織_4
func (h TraitHelper) GetPositionTraitOrgTrendLegalLicenceExists(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjOrgTrendLegalLicenceExists).Get(id).GetUserSideName()
}

// GetPositionTraitOrgTrendRelatedWithEngineer ポジション特徴_組織_5
func (h TraitHelper) GetPositionTraitOrgTrendRelatedWithEngineer(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjOrgTrendRelatedWithEngineer).Get(id).GetUserSideName()
}

// GetPositionTraitWorkEnvironment ポジション特徴_労働環境
func (h TraitHelper) GetPositionTraitWorkEnvironment(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjWorkEnvironment).Get(id).GetUserSideName()
}

// GetPositionTraitDevelopmentTerm ポジション特徴_開発スパン
func (h TraitHelper) GetPositionTraitDevelopmentTerm(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjDevelopmentTerm).Get(id).GetUserSideName()
}

// GetPositionTraitEmergencySupport ポジション特徴_緊急対応
func (h TraitHelper) GetPositionTraitEmergencySupport(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjEmergencySupport).Get(id).GetUserSideName()
}

// GetPositionTraitEmploymentToRegularEmployee 契約形態_正社員登用
func (h TraitHelper) GetPositionTraitEmploymentToRegularEmployee(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PteEmploymentToRegularEmployee).Get(id).GetUserSideName()
}

// GetPositionTraitProbation ポジション特徴_試用期間
func (h TraitHelper) GetPositionTraitProbation(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PteProbation).Get(id).GetUserSideName()
}

// GetPositionTraitContractPeriod ポジション特徴_契約期間
func (h TraitHelper) GetPositionTraitContractPeriod(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PteContractPeriod).Get(id).GetUserSideName()
}

// GetPositionTraitContractRenewal ポジション特徴_契約更新
func (h TraitHelper) GetPositionTraitContractRenewal(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PteContractRenewal).Get(id).GetUserSideName()
}

// GetPositionTraitContractExtension ポジション特徴_契約延長
func (h TraitHelper) GetPositionTraitContractExtension(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PteContractExtension).Get(id).GetUserSideName()
}

// GetPositionTraitSmokeFree 受動喫煙対策
func (h TraitHelper) GetPositionTraitSmokeFree(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxSmokeFree).Get(id).GetUserSideName()
}

// GetPositionTraitSmokeFreeEnvironment 受動喫煙対策（具体的な対策）
func (h TraitHelper) GetPositionTraitSmokeFreeEnvironment(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxSmokeFreeEnvironment).Get(id).GetUserSideName()
}

// GetPositionTraitEmploymentTypeChange 契約形態変更可否
func (h TraitHelper) GetPositionTraitEmploymentTypeChange(id int) string {
	return master.Provider().GetTraitPositionOptionsForUser(master.PteEmploymentTypeChange).Get(id).GetUserSideName()
}

// GetPositionTraitAccomplishmentImportances ポジション特徴_業績目標達成思考 全項目
func (h TraitHelper) GetPositionTraitAccomplishmentImportances() []*master.TraitPositionOptionForUser {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjAccomplishmentImportance)
}

// GetPositionTraitDevelopmentProcesses ポジション特徴_開発手法 全項目
func (h TraitHelper) GetPositionTraitDevelopmentProcesses() []*master.TraitPositionOptionForUser {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtjDevelopmentProcess)
}

// GetPositionTraitSmokeFrees 受動喫煙対策 全項目
func (h TraitHelper) GetPositionTraitSmokeFrees() []*master.TraitPositionOptionForUser {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxSmokeFree)
}

// GetPositionTraitSmokeFreeEnvironments 受動喫煙対策（具体的な対策） 全項目
func (h TraitHelper) GetPositionTraitSmokeFreeEnvironments() []*master.TraitPositionOptionForUser {
	return master.Provider().GetTraitPositionOptionsForUser(master.PtxSmokeFreeEnvironment)
}
