package master

//go:generate go run $GOPATH/src/miidas/domain/connect/enum/decorator/enumDecorator.go -type=MasterTraitCompanyID

type MasterTraitCompanyID string

const (
	CtxIsProfitCompany              MasterTraitCompanyID = "ctx_is_profit_company"                 // 企業概要_法人種別
	CtxEmployeeQty                  MasterTraitCompanyID = "ctx_employee_qty"                      // 企業概要_従業員数
	CtxYearsOfEstablishment         MasterTraitCompanyID = "ctx_years_of_establishment"            // 企業概要_設立
	CtxCapitalType                  MasterTraitCompanyID = "ctx_capital_type"                      // 企業概要_資本区分
	CtxSalesScale                   MasterTraitCompanyID = "ctx_sales_scale"                       // 企業概要_売上規模
	CtxPresidentName                MasterTraitCompanyID = "ctx_president_name"                    // 企業概要_代表者名
	CtxWebsite                      MasterTraitCompanyID = "ctx_website"                           // 企業概要_HP
	CtxIntroduction                 MasterTraitCompanyID = "ctx_introduction"                      // 企業概要_簡易企業紹介文
	CtxAppealPoint                  MasterTraitCompanyID = "ctx_appeal_point"                      // 企業概要_当社のアピールポイント
	CtxSalesOverseasRate            MasterTraitCompanyID = "ctx_sales_overseas_rate"               // 事業概要_海外売上比率
	CtxEmployeeWorkAbroadRate       MasterTraitCompanyID = "ctx_employee_work_abroad_rate"         // 社員属性_海外駐在社員比率
	CtxWelfareBenefit               MasterTraitCompanyID = "ctx_welfare__benefit"                  // 待遇_福利厚生（待遇編）
	CtxWelfareInsurance             MasterTraitCompanyID = "ctx_welfare__insurance"                // 福利厚生_社会保険
	CtxYearHolidays                 MasterTraitCompanyID = "ctx_year_holidays"                     // 休日休暇_年間休日
	CtxVacations                    MasterTraitCompanyID = "ctx_vacations"                         // 休日休暇_福利厚生（休日休暇編）
	CtxSideBusiness                 MasterTraitCompanyID = "ctx_side_business"                     // 副業
	CtxSideBusinessCondition        MasterTraitCompanyID = "ctx_side_business_condition"           // 副業条件
	CtxPaidHolidayUseRate           MasterTraitCompanyID = "ctx_paid_holiday_use_rate"             // 休日休暇_有給休暇取得率
	CtxJobRotationExists            MasterTraitCompanyID = "ctx_job_rotation_exists"               // キャリア_ジョブローテーション
	CtxChangeDepartmentRequest      MasterTraitCompanyID = "ctx_change_department_request"         // キャリア_異動希望申請制度
	CtxSpecialistCareerPath         MasterTraitCompanyID = "ctx_specialist_career_path"            // キャリア_スペシャリストキャリアパス
	CtxHREvaluationSpecialSystem    MasterTraitCompanyID = "ctx_hr_evaluation__special_system"     // 人事評価_特殊な評価制度
	CtxHREvaluationWomanManagerRate MasterTraitCompanyID = "ctx_hr_evaluation__woman_manager_rate" // 人事評価_人事評価実績_女性管理職比率
	CtxHREvaluation20SManagerRate   MasterTraitCompanyID = "ctx_hr_evaluation__20s_manager_rate"   // 人事評価_人事評価実績_20代管理職
	CtxTrainingSystemExists         MasterTraitCompanyID = "ctx_training_system_exists"            // 福利厚生_研修制度
	CtxTrainingSystemText           MasterTraitCompanyID = "ctx_training_system_text"              // 福利厚生_研修内容
	CtxWelfareAchievement           MasterTraitCompanyID = "ctx_welfare__achievement"              // 福利厚生_実績のある福利厚生
	CtxWelfarePopular               MasterTraitCompanyID = "ctx_welfare__popular"                  // 福利厚生_人気の福利厚生
	CtxWelfareOther                 MasterTraitCompanyID = "ctx_welfare__other"                    // 福利厚生_その他福利厚生
	CtxOther                        MasterTraitCompanyID = "ctx_other"                             // その他企業特徴
	CtxPR                           MasterTraitCompanyID = "ctx_pr"                                // 企業PRスペース
)

const (

	// 年間休日
	CtxYearHolidaysLt120Days = 1 // 120日未満
	CtxYearHolidaysGe120Days = 2 // 120日以上
	CtxYearHolidaysGe130Days = 3 // 130日以上
	CtxYearHolidaysGe140Days = 4 // 140日以上

	// 海外売上比率
	CtxSalesOverseasRateNoExpandPlan = 1 // なし（海外展開する予定なし）
	CtxSalesOverseasRateExpandPlan   = 2 // なし（海外展開する予定あり）

	// 当社のアピールポイント
	CtxCompanyAppealStableStage = 1  // 安定した事業
	CtxCompanyAppealVenture     = 12 // ベンチャー企業

	// 資本区分
	CtxCapitalTypeListed  = 1 // 上場企業
	CtxCapitalTypeForeign = 4 // 外資系企業
)
