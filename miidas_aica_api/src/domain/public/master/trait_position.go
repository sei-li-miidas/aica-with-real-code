package master

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=MasterTraitPositionID

type MasterTraitPositionID string

const (
	PtxTitle                             MasterTraitPositionID = "ptx_title"                                 // ポジション名（公開用）
	PtxPost                              MasterTraitPositionID = "ptx_post"                                  // 役職
	PtxEmploymentType                    MasterTraitPositionID = "ptx_employment_type"                       // 契約形態
	PtxJob                               MasterTraitPositionID = "ptx_job"                                   // 仕事内容
	PtxJobText                           MasterTraitPositionID = "ptx_job_text"                              // 仕事内容_テキスト
	PtxModelAnnualIncome                 MasterTraitPositionID = "ptx_model_annual_income"                   // 待遇_モデル年収（目安）
	PtxStockOption                       MasterTraitPositionID = "ptx_stock_option"                          // 待遇_ストックオプション
	PtxBonusCount                        MasterTraitPositionID = "ptx_bonus_count"                           // 待遇_賞与
	PtxPromotionCount                    MasterTraitPositionID = "ptx_promotion_count"                       // 待遇_昇給・昇格
	PtxWorkAddress                       MasterTraitPositionID = "ptx_work_address"                          // 勤務地_都道府県
	PtxRemoteWork                        MasterTraitPositionID = "ptx_remote_work"                           // リモート勤務
	PtxRemoteWorkOfficeFrequency         MasterTraitPositionID = "ptx_remote_work_office_frequency"          // リモート勤務_出社頻度
	PtxHoliday                           MasterTraitPositionID = "ptx_holiday"                               // 休日
	PtxWorkTime                          MasterTraitPositionID = "ptx_worktime"                              // 勤務時間
	PtxWorkTimeText                      MasterTraitPositionID = "ptx_worktime_text"                         // 勤務時間_テキスト
	PtxWorkTimeNightShift                MasterTraitPositionID = "ptx_worktime_night_shift"                  // 勤務時間_夜勤の有無
	PtxOvertimeAvg                       MasterTraitPositionID = "ptx_overtime_avg"                          // 労働環境_平均残業時間
	PtxOfficialTripFrequency             MasterTraitPositionID = "ptx_official_trip_frequency"               // 労働環境_出張頻度
	PtxWorkingEnvironment                MasterTraitPositionID = "ptx_working_environment"                   // 労働環境_労働環境の特徴
	PtxTransferenceExists                MasterTraitPositionID = "ptx_transference_exists"                   // キャリア_国内転勤の有無
	PtxTransferenceFrequency             MasterTraitPositionID = "ptx_transference_frequency"                // キャリア_国内転勤の有無_国内転勤の頻度
	PtxTransferenceAbroadExists          MasterTraitPositionID = "ptx_transference_abroad_exists"            // キャリア_海外転勤
	PtxTransferenceAbroadEnglishIsUnused MasterTraitPositionID = "ptx_transference_abroad_english_is_unused" // キャリア_海外転勤_英語力不問
	PtxBusiness                          MasterTraitPositionID = "ptx_business"                              // 事業
	PtxSmokeFree                         MasterTraitPositionID = "ptx_smoke_free"                            // 受動喫煙対策
	PtxSmokeFreeEnvironment              MasterTraitPositionID = "ptx_smoke_free_environment"                // 受動喫煙対策（具体的な対策）
	PtxHREvaluationType                  MasterTraitPositionID = "ptx_hr_evaluation_type"                    // 人事評価_評価基準の特徴_1
	PtxHREvaluationCompetency            MasterTraitPositionID = "ptx_hr_evaluation__competency"             // 人事評価_特に評価されるコンピテンシー
	PtxPR                                MasterTraitPositionID = "ptx_pr"                                    // その他_ポジションPR
	PtjAccomplishmentImportance          MasterTraitPositionID = "ptj_accomplishment_importance"             // ポジション特徴_業績目標達成思考
	PtjAccomplishmentRate                MasterTraitPositionID = "ptj_accomplishment_rate"                   // ポジション特徴_業績目標達成者率
	PtjSalesStyleDive                    MasterTraitPositionID = "ptj_sales_style__dive"                     // ポジション特徴_営業スタイル_新規飛び込み
	PtjSalesStyleTelAppointment          MasterTraitPositionID = "ptj_sales_style__tel_appointment"          // ポジション特徴_営業スタイル_新規テレアポ
	PtjSalesStyleHost                    MasterTraitPositionID = "ptj_sales_style__host"                     // ポジション特徴_営業スタイル_接待
	PtjCareerPathOutOfSiteExists         MasterTraitPositionID = "ptj_career_path__out_of_site_exists"       // ポジション特徴_キャリアパス_1
	PtjCareerPathWorkHeadOfficeExists    MasterTraitPositionID = "ptj_career_path__work_head_office_exists"  // ポジション特徴_キャリアパス_2
	PtjOrgTrendEngineerManagerExists     MasterTraitPositionID = "ptj_org_trend__engineer_manager_exists"    // ポジション特徴_組織_1
	PtjOrgTrendSectionMemberQty          MasterTraitPositionID = "ptj_org_trend__section_member_qty"         // ポジション特徴_組織_2
	PtjOrgTrendAccountingLicenceExists   MasterTraitPositionID = "ptj_org_trend__accounting_licence_exists"  // ポジション特徴_組織_3
	PtjOrgTrendLegalLicenceExists        MasterTraitPositionID = "ptj_org_trend__legal_licence_exists"       // ポジション特徴_組織_4
	PtjOrgTrendRelatedWithEngineer       MasterTraitPositionID = "ptj_org_trend__related_with_engineer"      // ポジション特徴_組織_5
	PtjWorkEnvironment                   MasterTraitPositionID = "ptj_work_environment"                      // ポジション特徴_労働環境
	PtjDevelopmentTerm                   MasterTraitPositionID = "ptj_development_term"                      // ポジション特徴_開発スパン
	PtjDevelopmentProcess                MasterTraitPositionID = "ptj_development_process"                   // ポジション特徴_開発手法
	PtjEmergencySupport                  MasterTraitPositionID = "ptj_emergency_support"                     // ポジション特徴_緊急対応
	PteJoinedReserve                     MasterTraitPositionID = "pte_joined_reserve"                        // 待遇_入社支度金
	PteEmploymentToRegularEmployee       MasterTraitPositionID = "pte_employment_to_regular_employee"        // 契約形態_正社員登用
	PteEmploymentTypeChange              MasterTraitPositionID = "pte_employment_type_change"                // 契約形態変更可否
	PteProbation                         MasterTraitPositionID = "pte_probation"                             // ポジション特徴_試用期間
	PteContractPeriod                    MasterTraitPositionID = "pte_contract_period"                       // ポジション特徴_契約期間
	PteContractExtension                 MasterTraitPositionID = "pte_contract_extension"                    // ポジション特徴_契約延長
	PteWorkplace                         MasterTraitPositionID = "pte_workplace"                             // ポジション特徴_作業場所
	PteContractRenewal                   MasterTraitPositionID = "pte_contract_renewal"                      // ポジション特徴_契約更新
	PteContractRenewalText               MasterTraitPositionID = "pte_contract_renewal_text"                 // ポジション特徴_契約更新の詳細テキスト
	PteRegularOutsourcing                MasterTraitPositionID = "pte_regular_outsourcing"                   // 業務委託（レギュラー）
	PteSpotOutsourcing                   MasterTraitPositionID = "pte_spot_outsourcing"                      // 業務委託（スポット）
	PteSpotJobRequest                    MasterTraitPositionID = "pte_spot_job_request"                      // 業務委託（スポット）依頼内容
	PteCommissionBusinessDescription     MasterTraitPositionID = "pte_commission_business_description"       // 業務委託（完全歩合制）業務内容
	PteCommissionFeeCondition            MasterTraitPositionID = "pte_commission_fee_condition"              // 業務委託（完全歩合制）報酬
	PteBaseMonthlySalary                 MasterTraitPositionID = "pte_base_monthly_salary"                   // ポジション特徴_基本月給
	PteOvertimeSalary                    MasterTraitPositionID = "pte_overtime_salary"                       // ポジション特徴_固定残業代
)
