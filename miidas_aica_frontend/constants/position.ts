import { COMPETENCY_ITEM } from "./competency/competency";
import * as ICON from "./icon";

// モデル年収
export const MODEL_ANNUAL_INCOME = {
  KEYS: {
    // 値格納マップのキー
    TWENTIES: {
      // 20代
      ID: "Income20s",
      Label: "20代",
    },
    THIRTIES: {
      // 30代
      ID: "Income30s",
      Label: "30代",
    },
    FORTIES: {
      // 40代
      ID: "Income40s",
      Label: "40代",
    },
  },
  INCOMES: [
    { ID: 200, Name: "200万円以下" },
    { ID: 250, Name: "250万円" },
    { ID: 300, Name: "300万円" },
    { ID: 350, Name: "350万円" },
    { ID: 400, Name: "400万円" },
    { ID: 450, Name: "450万円" },
    { ID: 500, Name: "500万円" },
    { ID: 550, Name: "550万円" },
    { ID: 600, Name: "600万円" },
    { ID: 650, Name: "650万円" },
    { ID: 700, Name: "700万円" },
    { ID: 750, Name: "750万円" },
    { ID: 800, Name: "800万円" },
    { ID: 850, Name: "850万円" },
    { ID: 900, Name: "900万円" },
    { ID: 950, Name: "950万円" },
    { ID: 1000, Name: "1000万円以上" },
  ],
  SEARCH_INCOMES: [
    { ID: 250, Name: "250万円以上" },
    { ID: 300, Name: "300万円以上" },
    { ID: 350, Name: "350万円以上" },
    { ID: 400, Name: "400万円以上" },
    { ID: 450, Name: "450万円以上" },
    { ID: 500, Name: "500万円以上" },
    { ID: 550, Name: "550万円以上" },
    { ID: 600, Name: "600万円以上" },
    { ID: 650, Name: "650万円以上" },
    { ID: 700, Name: "700万円以上" },
    { ID: 750, Name: "750万円以上" },
    { ID: 800, Name: "800万円以上" },
    { ID: 850, Name: "850万円以上" },
    { ID: 900, Name: "900万円以上" },
    { ID: 950, Name: "950万円以上" },
    { ID: 1000, Name: "1000万円以上" },
  ],
} as const;

// 契約形態
export const TRAIT_EMPLOYMENT_TYPE = {
  EMPLOYEE: 1, // 正社員
  CONTRACT: 2, // 契約社員
  /**
   * NOTE: 役員は除外する（レギュラー・スポット追加以前に求人に設定できた項目。バックエンド都合でレスポンスに含まれる）
   */
  OFFICER: 3, // 役員（任用契約）
  OUTSOURCING_REGULAR: 4, // 業務委託契約（レギュラー）
  OUTSOURCING_SPOT: 5, // 業務委託契約（スポット）
  OUTSOURCING_COMMISSION: 6, // 業務委託契約（完全歩合制）
} as const;

// 契約形態の説明
export const TRAIT_EMPLOYMENT_TYPE_DESCRIPTION = {
  EMPLOYEE:
    "労働契約に期間の定めがない雇用形態。就業規則に明記された所定労働時間がフルタイムとなる。雇用保険・社会保険は原則完備。", // 正社員
  CONTRACT:
    "予め雇用期間を定めた労働契約（有期労働契約）を結ぶ雇用形態。雇用期間は最長で原則3年。\n※専門職や60歳以上との契約では最長5年。", // 契約社員
  REGULAR:
    "企業に直接雇用されるのではなく、業務内容、報酬、期日などを事前に取り決めて業務を遂行する働き方です。フリーランスの方や副業として仕事を受けたい方向けです。\nミイダスでは、契約期間が1ヶ月以上の業務を「レギュラー」と表しています。", // 業務委託契約（レギュラー・スポット）
  SPOT: "企業に直接雇用されるのではなく、業務内容、報酬、期日などを事前に取り決めて業務を遂行する働き方です。フリーランスの方や副業として仕事を受けたい方向けです。\nミイダスでは、契約期間が1ヶ月未満の業務を「スポット」と表しています。", // 業務委託契約（レギュラー・スポット）
  COMMISSION:
    "報酬がすべて成果に応じて支払われる契約です。固定報酬はありません。専門知識やスキルを生かして、成果次第で収入を上げることができます。\n\n例）営業成績や売上に応じた報酬、デザイナー・ライター業は納品数に応じた報酬など", // 業務委託契約（完全歩合制）
  REGULAR_DETAIL:
    "1ヵ月以上の長期契約を結ぶ業務委託です。高度な知識・技術を求められる業務も多く、報酬は月額制です。",
  SPOT_DETAIL:
    "最短1時間から働ける短期の業務委託です。一定の専門知識を求められる業務も多く、報酬は時給制です。",
  COMMISSION_DETAIL:
    "固定報酬はなく、成果に応じて報酬が支払われる業務委託契約です。成果によっては高収入も可能です。",
} as const;

/**
 * トレイト求人一覧
 *
 * トレイト編集・表示画面において、Viewの組み立てやTraitレコードとのマッピングに用いる
 * （AppealなどはTraitレコードに含まれるので、すべてTraitレコードに含めて定数はIDだけにしてもいいかもしれない）
 *
 * IDのプレフィックス（ptx_など）について
 * ct：企業特徴、pt:求人特徴、bt:事業内容
 * 共通ー＞x
 * 業種ごとのものー＞i
 * 職種ごとのものー＞j
 * 契約形態ごとのものー＞e
 *
 *  ID                   : トレイトID
 *  Name                 : トレイト項目名
 */
export const TRAITS = {
  PTX_TITLE: {
    ID: "ptx_title",
    Name: "公開求人名",
  },
  PTX_POST: {
    ID: "ptx_post",
    Name: "役職",
  },
  PTX_BUSINESS: {
    ID: "ptx_business",
    Name: "事業",
  },
  PTX_EMPLOYMENT_TYPE: {
    ID: "ptx_employment_type",
    Name: "契約形態",
  },
  PTX_JOB: {
    ID: "ptx_job",
    Name: "仕事内容",
  },
  PTX_JOB_TEXT: {
    ID: "ptx_job_text",
    Name: "仕事内容（詳細）",
  },
  PTX_GUARANTEED_INCOME: {
    ID: "ptx_guaranteed_income",
    Name: "確約年収",
  },
  PTX_MODEL_ANNUAL_INCOME: {
    ID: "ptx_model_annual_income",
    Name: "モデル年収",
  },
  PTE_BASE_MONTHLY_SALARY: {
    ID: "pte_base_monthly_salary",
    Name: "基本月給",
  },
  PTE_OVERTIME_SALARY: {
    ID: "pte_overtime_salary",
    Name: "固定残業代",
  },
  PTX_STOCK_OPTION: {
    ID: "ptx_stock_option",
    Name: "ストックオプション",
  },
  PTX_BONUS_COUNT: {
    ID: "ptx_bonus_count",
    Name: "賞与",
  },
  PTX_PROMOTION_COUNT: {
    ID: "ptx_promotion_count",
    Name: "昇給・昇格",
  },
  PTX_WORK_ADDRESS: {
    ID: "ptx_work_address",
    Name: "勤務地",
  },
  PTX_REMOTE_WORK: {
    ID: "ptx_remote_work",
    Name: "リモート勤務",
  },
  PTX_REMOTE_WORK_CONDITION: {
    ID: "ptx_remote_work_condition",
    Name: "リモート勤務の条件",
  },
  PTX_REMOTE_WORK_OFFICE_FREQUENCY: {
    ID: "ptx_remote_work_office_frequency",
    Name: "リモート勤務の出社頻度",
  },
  PTX_HOLIDAY: {
    ID: "ptx_holiday",
    Name: "休日",
  },
  PTX_WORKTIME_TEXT: {
    ID: "ptx_worktime_text",
    Name: "勤務時間",
  },
  PTX_WORKTIME: {
    ID: "ptx_worktime",
    Name: "勤務時間",
  },
  PTX_WORKTIME_NIGHT_SHIFT: {
    ID: "ptx_worktime_night_shift",
    Name: "勤務時間",
  },
  PTX_OVERTIME_AVG: {
    ID: "ptx_overtime_avg",
    Name: "平均残業時間",
  },
  PTX_OFFICIAL_TRIP_FREQUENCY: {
    ID: "ptx_official_trip_frequency",
    Name: "出張頻度",
  },
  PTX_WORKING_ENVIRONMENT: {
    ID: "ptx_working_environment",
    Name: "労働環境の特徴",
  },
  PTX_TRANSFERENCE_EXISTS: {
    ID: "ptx_transference_exists",
    Name: "国内転勤",
  },
  // PTX_TRANSFERENCE_EXISTS に依存
  PTX_TRANSFERENCE_FREQUENCY: {
    ID: "ptx_transference_frequency",
    Name: "国内転勤の頻度",
  },
  PTX_TRANSFERENCE_ABROAD_EXISTS: {
    ID: "ptx_transference_abroad_exists",
    Name: "海外転勤",
  },
  // PTX_TRANSFERENCE_ABROAD_EXISTS に依存
  PTX_TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED: {
    ID: "ptx_transference_abroad_english_is_unused",
    Name: "英語力",
  },
  // 人事評価
  PTX_HR_EVALUATION__COMPETENCY: {
    ID: "ptx_hr_evaluation__competency",
    Name: "特に評価されるコンピテンシー",
  },
  PTX_HR_EVALUATION_TYPE: {
    ID: "ptx_hr_evaluation_type",
    Name: "評価基準の特徴",
  },
  PTX_PR: {
    ID: "ptx_pr",
    Name: "求人PR",
  },
  PTX_SMOKE_FREE: {
    ID: "ptx_smoke_free",
    Name: "受動喫煙対策",
  },
  // PTX_SMOKE_FREE に依存
  PTX_SMOCK_FREE_ENVIRONMENT: {
    ID: "ptx_smoke_free_environment",
    Name: "受動喫煙対策（具体的な対策）",
  },
  PTE_JOINED_RESERVE: {
    ID: "pte_joined_reserve",
    Name: "入社支度金",
  },
  PTJ_ACCOMPLISHMENT_RATE: {
    ID: "ptj_accomplishment_rate",
    Name: "業績目標達成者率",
  },
  PTJ_SALES_STYLE__DIVE: {
    ID: "ptj_sales_style__dive",
    Name: "新規飛び込み",
  },
  PTJ_SALES_STYLE__TEL_APPOINTMENT: {
    ID: "ptj_sales_style__tel_appointment",
    Name: "新規テレアポ",
  },
  PTJ_SALES_STYLE__HOST: {
    ID: "ptj_sales_style__host",
    Name: "接待",
  },
  PTJ_CAREER_PATH__OUT_OF_SITE_EXISTS: {
    ID: "ptj_career_path__out_of_site_exists",
    Name: "キャリアパス",
  },
  PTJ_CAREER_PATH__WORK_HEAD_OFFICE_EXISTS: {
    ID: "ptj_career_path__work_head_office_exists",
    Name: "キャリアパス",
  },
  PTJ_ORG_TREND__ENGINEER_MANAGER_EXISTS: {
    ID: "ptj_org_trend__engineer_manager_exists",
    Name: "組織",
  },
  PTJ_ORG_TREND__SECTION_MEMBER_QTY: {
    ID: "ptj_org_trend__section_member_qty",
    Name: "組織",
  },
  PTJ_ORG_TREND__ACCOUNTING_LICENCE_EXISTS: {
    ID: "ptj_org_trend__accounting_licence_exists",
    Name: "組織",
  },
  PTJ_ORG_TREND__LEGAL_LICENCE_EXISTS: {
    ID: "ptj_org_trend__legal_licence_exists",
    Name: "組織",
  },
  PTJ_ORG_TREND__RELATED_WITH_ENGINEER: {
    ID: "ptj_org_trend__related_with_engineer",
    Name: "組織",
  },
  PTJ_WORK_ENVIRONMENT: {
    ID: "ptj_work_environment",
    Name: "労働環境",
  },
  PTJ_DEVELOPMENT_TERM: {
    ID: "ptj_development_term",
    Name: "開発スパン",
  },
  PTJ_DEVELOPMENT_PROCESS: {
    ID: "ptj_development_process",
    Name: "開発手法",
  },
  PTJ_EMERGENCY_SUPPORT: {
    ID: "ptj_emergency_support",
    Name: "緊急対応",
  },
  PTE_EMPLOYMENT_TO_REGULAR_EMPLOYEE: {
    ID: "pte_employment_to_regular_employee",
    Name: "正社員登用",
  },
  PTE_PROBATION: {
    ID: "pte_probation",
    Name: "試用期間",
  },
  PTE_CONTRACT_PERIOD: {
    ID: "pte_contract_period",
    Name: "契約期間",
  },
  PTE_CONTRACT_RENEWAL: {
    ID: "pte_contract_renewal",
    Name: "契約更新",
  },
  PTE_CONTRACT_RENEWAL_TEXT: {
    ID: "pte_contract_renewal_text",
    Name: "契約更新の詳細",
  },
  PTE_CONTRACT_EXTENSION: {
    ID: "pte_contract_extension",
    Name: "契約延長",
  },
  CONTRACT_RENEWAL: {
    ID: "pte_contract_renewal",
    Name: "契約更新",
  },
  CONTRACT_RENEWAL_TEXT: {
    ID: "pte_contract_renewal_text",
    Name: "契約更新の詳細",
  },
  PTE_WORKPLACE: {
    ID: "pte_workplace",
    Name: "作業場所",
  },
  PTE_REGULAR_OUTSOURCING: {
    ID: "pte_regular_outsourcing",
    Name: "業務委託（レギュラー）",
  },
  PTE_SPOT_OUTSOURCING: {
    ID: "pte_spot_outsourcing",
    Name: "業務委託（スポット）",
  },
  PTE_SPOT_JOB_REQUEST: {
    ID: "pte_spot_job_request",
    Name: "依頼内容",
  },
  PTE_SPOT_JOB_DESCRIPTION: {
    ID: "pte_spot_job_description",
    Name: "依頼内容（詳細）",
  },
  PTE_COMMISSION_BUSINESS_DESCRIPTION: {
    ID: "pte_commission_business_description",
    Name: "業務内容",
  },
  PTE_COMMISSION_FEE_CONDITION: {
    ID: "pte_commission_fee_condition",
    Name: "報酬",
  },
} as const;

// 求人詳細項目
export const POSITION_DETAIL = {
  TITLE: {
    // 求人名（公開用） (旧 ptx_title )
    ID: "Title",
    Name: "公開求人名",
  },
  POST: {
    // 役職 (旧 ptx_post )
    ID: "Post",
    Name: "役職",
  },
  EMPLOYMENT_TYPE: {
    // 契約形態種別 (旧 ptx_employment_type )
    ID: "EmploymentType",
    Name: "契約形態",
  },
  JOBS: {
    // 仕事内容 (旧 ptx_job )
    ID: "Jobs",
    Name: "仕事内容",
  },
  MAIN_JOB_TEXT: {
    // 仕事内容(メイン) (旧 ptx_job_text )
    ID: "MainJobText",
    Name: "仕事内容（詳細）",
  },
  JOB_CHANGE: {
    // 確約年収 (旧 ptx_guaranteed_income ) 求人受信時は求人年収、未受信の場合はnull
    ID: "JobChange",
    Name: "確約年収",
  },
  MODEL_ANNUAL_INCOME: {
    // モデル年収 (旧 ptx_model_annual_income )
    ID: "ModelAnnualIncome",
    Name: "モデル年収",
  },
  BASE_MONTHLY_SALARY: {
    // 基本月給 (旧 pte_base_monthly_salary )
    ID: "BaseMonthlySalary",
    Name: "基本月給",
  },
  OVERTIME_SALARY: {
    // 固定残業代
    ID: "OvertimeSalary",
    Name: "固定残業代",
  },
  STOCK_OPTION: {
    // ストックオプション (旧 ptx_stock_option )
    ID: "StockOption",
    Name: "ストックオプション",
  },
  BONUS_COUNT: {
    // 賞与 (旧 ptx_bonus_count)
    ID: "BonusCount",
    Name: "賞与",
  },
  PROMOTION_COUNT: {
    // 昇給・昇格 (旧 ptx_promotion_count )
    ID: "PromotionCount",
    Name: "昇給・昇格",
  },
  WORK_ADDRESS: {
    // 勤務地都道府県 (旧 ptx_work_address )
    ID: "WorkAddress",
    Name: "勤務地",
  },
  REMOTE_WORK: {
    // リモート勤務 (旧 ptx_remote_work )
    ID: "RemoteWork",
    Name: "リモート勤務",
  },
  REMOTE_WORK_CONDITION: {
    // リモート勤務条件 (旧 ptx_remote_work_condition )
    ID: "RemoteWorkCondition",
    Name: "リモート勤務の条件",
  },
  REMOTE_WORK_OFFICE_FREQUENCY: {
    // リモート勤務出社頻度 (旧 ptx_remote_work_office_frequency )
    ID: "RemoteWorkOfficeFrequency",
    Name: "リモート勤務の出社頻度",
  },
  HOLIDAY: {
    // 休日 (旧 ptx_holiday )
    ID: "Holiday",
    Name: "休日",
  },
  WORK_TIME: {
    // 勤務時間テキスト (旧 ptx_worktime_text )
    ID: "WorkTime",
    Name: "勤務時間",
  },
  WORK_TIME_SYSTEM: {
    // 勤務時間 (旧 ptx_worktime )
    ID: "WorkTimeSystem",
    Name: "勤務時間",
  },
  WORK_TIME_NIGHTS_SHIFT: {
    // 勤務時間夜勤の有無 (旧 ptx_worktime_night_shift )
    ID: "WorkTimeNightsShift",
    Name: "勤務時間",
  },
  OVERTIME_AVG: {
    // 労働環境平均残業時間 (旧 ptx_overtime_avg )
    ID: "OvertimeAvg",
    Name: "平均残業時間",
  },
  OFFICIAL_TRIP_FREQUENCY: {
    // 労働環境出張頻度 (旧 ptx_official_trip_frequency )
    ID: "OfficialTripFrequency",
    Name: "出張頻度",
  },
  WORK_ENVIRONMENT: {
    // 労働環境労働環境の特徴 (旧 ptx_working_environment )
    ID: "WorkEnvironment",
    Name: "労働環境の特徴",
  },
  TRANSFERENCE_EXISTS: {
    // キャリア国内転勤の有無 (旧 ptx_transference_exists )
    ID: "TransferenceExists",
    Name: "国内転勤",
  },
  // TransferenceExists に依存
  TRANSFERENCE_FREQUENCY: {
    // キャリア国内転勤の有無国内転勤の頻度 (旧 ptx_transference_frequency )
    ID: "TransferenceFrequency",
    Name: "国内転勤の頻度",
  },
  TRANSFERENCE_ABROAD_EXISTS: {
    // キャリア海外転勤 (旧 ptx_transference_abroad_exists )
    ID: "TransferenceAbroadExists",
    Name: "海外転勤",
  },
  // TransferenceAbroadExists に依存
  TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED: {
    ID: "TransferenceAbroadEnglishIsUnused",
    Name: "英語力",
  },
  // 人事評価
  HR_EVALUATION_COMPETENCY: {
    // 人事評価特に評価されるコンピテンシー (旧 ptx_hr_evaluation__competency )
    ID: "HREvaluationCompetency",
    Name: "特に評価されるコンピテンシー",
  },
  HR_EVALUATION_TYPE: {
    // 人事評価評価基準の特徴 (旧 ptx_hr_evaluation_type )
    ID: "HREvaluationType",
    Name: "評価基準の特徴",
  },
  PR: {
    // その他求人PR (旧 ptx_pr )
    ID: "PR",
    Name: "求人PR",
  },
  SMOKE_FREE: {
    ID: "SmokeFree",
    Name: "受動喫煙対策",
  },
  // SmokeFree に依存
  SMOKE_FREE_ENVIRONMENT: {
    ID: "SmokeFreeEnvironment",
    Name: "受動喫煙対策（具体的な対策）",
  },
  JOINED_RESERVE: {
    // 入社支度金 (旧 pte_joined_reserve )
    ID: "JoinedReserve",
    Name: "入社支度金",
  },
  ACCOMPLISHMENT_RATE: {
    // 求人特徴業績目標達成者率 (旧 ptj_accomplishment_rate )
    ID: "AccomplishmentRate",
    Name: "業績目標達成者率",
  },
  SALES_STYLE_DIVE: {
    // 求人特徴営業スタイル新規飛び込み (旧 ptj_sales_style__dive )
    ID: "SalesStyleDive",
    Name: "新規飛び込み",
  },
  SALES_STYLE_TEL_APPOINTMENT: {
    // 求人特徴営業スタイル新規テレアポ (旧 ptj_sales_style__tel_appointment )
    ID: "SalesStyleTelAppointment",
    Name: "新規テレアポ",
  },
  SALES_STYLE_HOST: {
    // 求人特徴営業スタイル接待 (旧 ptj_sales_style__host )
    ID: "SalesStyleHost",
    Name: "接待",
  },
  CAREER_PATH_OUT_OF_SITE_EXISTS: {
    // 求人特徴キャリアパス1 (旧 ptj_career_path__out_of_site_exists )
    ID: "CareerPathOutOfSiteExists",
    Name: "キャリアパス",
  },
  CAREER_PATH_WORK_HEAD_OFFICE_EXISTS: {
    // 求人特徴キャリアパス2 (旧 ptj_career_path__work_head_office_exists )
    ID: "CareerPathWorkHeadOfficeExists",
    Name: "キャリアパス",
  },
  ORG_TREND_ENGINEER_MANAGER_EXISTS: {
    // 求人特徴組織1 (旧 ptj_org_trend__engineer_manager_exists )
    ID: "OrgTrendEngineerManagerExists",
    Name: "組織",
  },
  ORG_TREND_SECTION_MEMBER_QTY: {
    // 求人特徴組織2 (旧 ptj_org_trend__section_member_qty )
    ID: "OrgTrendSectionMemberQty",
    Name: "組織",
  },
  ORG_TREND_ACCOUNTING_LICENCE_EXISTS: {
    // 求人特徴組織3 (旧 ptj_org_trend__accounting_licence_exists )
    ID: "OrgTrendAccountingLicenceExists",
    Name: "組織",
  },
  ORG_TREND_LEGAL_LICENCE_EXISTS: {
    // 求人特徴組織4 (旧 ptj_org_trend__legal_licence_exists )
    ID: "OrgTrendLegalLicenceExists",
    Name: "組織",
  },
  ORG_TREND_RELATED_WITH_ENGINEER: {
    // 求人特徴組織5 (旧 ptj_org_trend__related_with_engineer )
    ID: "OrgTrendRelatedWithEngineer",
    Name: "組織",
  },
  IT_ENGINEER_WORK_ENVIRONMENT: {
    // 求人特徴労働環境 (旧 ptj_work_environment )
    ID: "ITEngineerWorkEnvironment",
    Name: "労働環境",
  },
  DEVELOPMENT_TERM: {
    // 求人特徴開発スパン (旧 ptj_development_term )
    ID: "DevelopmentTerm",
    Name: "開発スパン",
  },
  DEVELOPMENT_PROCESS: {
    // 求人特徴開発手法 (旧 ptj_development_process )
    ID: "DevelopmentProcess",
    Name: "開発手法",
  },
  EMERGENCY_SUPPORT: {
    // 求人特徴緊急対応 (旧 ptj_emergency_support )
    ID: "EmergencySupport",
    Name: "緊急対応",
  },
  EMPLOYMENT_TO_REGULAR_EMPLOYEE: {
    // 契約形態契約社員 (旧 pte_employment_to_regular_employee )
    ID: "EmploymentToRegularEmployee",
    Name: "正社員登用",
  },
  PROBATION: {
    // 求人特徴試用期間 (旧 pte_probation )
    ID: "Probation",
    Name: "試用期間",
  },
  CONTRACT_PERIOD: {
    // 求人特徴契約期間 (旧 pte_contract_period )
    ID: "ContractPeriod",
    Name: "契約期間",
  },
  CONTRACT_RENEWAL: {
    // pte_contract_renewal
    ID: "ContractRenewal",
    Name: "契約更新",
  },
  CONTRACT_RENEWAL_TEXT: {
    // pte_contract_renewal_text
    ID: "ContractRenewalText",
    Name: "契約更新の詳細",
  },
  CONTRACT_EXTENSION: {
    // レギュラー求人: 契約延長 (旧 pte_contract_extension )
    ID: "ContractExtension",
    Name: "契約延長",
  },
  REGULAR_OUTSOURCING: {
    // 業務委託（レギュラー） (旧 pte_regular_outsourcing )
    ID: "RegularOutsourcing",
    Name: "業務委託（レギュラー）",
  },
  SPOT_OUTSOURCING: {
    // 業務委託（スポット） (旧 pte_spot_outsourcing )
    ID: "SpotOutsourcing",
    Name: "業務委託（スポット）",
  },
  SPOT_JOB_DESCRIPTION: {
    // 業務委託（スポット）依頼内容 (旧 pte_spot_job_description )
    ID: "SpotJobDescription",
    Name: "依頼内容",
  },
  COMMISSION_BUSINESS_DESCRIPTION: {
    // 業務委託（完全歩合制）業務内容 (旧 pte_commission_business_description )
    ID: "CommissionBusinessDescription",
    Name: "業務内容",
  },
  COMMISSION_FEE_CONDITION: {
    // 業務委託（完全歩合制）報酬 (旧 pte_commission_fee_condition )
    ID: "CommissionFeeCondition",
    Name: "報酬",
  },
} as const;

// トレイトオプションの値
export const TRAIT_OPTION_VALUES = {
  REMOTE_WORK: {
    /** リモート勤務NG */
    NG: 1,
    /** リモート勤務OK（条件つき） */
    OK_WITH_RULE: 2,
    /** リモート勤務OK（条件なし） */
    OK: 3,
  },
  TRANSFERENCE_ABROAD_ENGLISH_IS_UNUSED: {
    /** 必須 */
    REQUIRED: 1,
    /** 必須ではない */
    NOT_REQUIRED: 2,
  },
  SMOKE_FREE: {
    /** あり */
    EXIST: 1,
    /** なし */
    NONE: 2,
  },
  OVERTIME_AVG: {
    /** 原則なし */
    NONE: 1,
    /** 月10時間以内 */
    UNDER_10H: 2,
    /** 月20時間以内 */
    UNDER_20H: 3,
    /** 月30時間以内 */
    UNDER_30H: 4,
    /** 月40時間以内 */
    UNDER_40H: 5,
    /** 月40時間以上 */
    OVER_40H: 6,
  },
  WORK_TIME_SYSTEM: {
    /** 勤務時間固定制 */
    FIXED: 1,
    /** シフト制 */
    SHIFT: 2,
  },
} as const;

// トレイトオプションのヘルプ一覧
export const TRAIT_OPTION_HELPS = {
  // 休日
  ptx_holiday: {
    2: {
      title: "完全週休2日制",
      text: "完全週休2日制とは、1年を通して、毎週2日の休日があること",
    },
    3: {
      title: "週休2日制",
      text: "週休2日制とは、1年を通して、月に1回以上2日の休みがある週があり、他の週は1日以上の休みがあること",
    },
  },
} as const;

// 上司の名前
export const BOSS_NAMES = ["A", "B", "C", "D", "E"];

type HrEvaluationCompetencyFeaturesItemsType = {
  [K in keyof typeof COMPETENCY_ITEM]: {
    Options: { Value: number; Name: string; Help: string }[];
  } & (typeof COMPETENCY_ITEM)[K];
};

/**
 * 特に評価されるコンピテンシーで使用するコンピテンシー項目
 */
export const HR_EVALUATION_COMPETENCY_FEATURES: HrEvaluationCompetencyFeaturesItemsType =
  {
    /** マネジメントスタイル */
    [COMPETENCY_ITEM.ManagementStyle.ID]: {
      ...COMPETENCY_ITEM.ManagementStyle,
      Options: [
        {
          Value: 1,
          Name: "短期的な目標達成を目指し適切に任せる",
          Help: COMPETENCY_ITEM.ManagementStyle.PointLowText,
        },
        {
          Value: 2,
          Name: "長期ビジョン達成を目指し具体的に指示する",
          Help: COMPETENCY_ITEM.ManagementStyle.PointHighText,
        },
      ],
    },
    /** リーダーシップ */
    [COMPETENCY_ITEM.Leadership.ID]: {
      ...COMPETENCY_ITEM.Leadership,
      Options: [
        {
          Value: 1,
          Name: "周囲のフォローにまわる",
          Help: COMPETENCY_ITEM.Leadership.PointLowText,
        },
        {
          Value: 2,
          Name: "先頭に立って周囲を牽引する",
          Help: COMPETENCY_ITEM.Leadership.PointHighText,
        },
      ],
    },
    /** 対人影響 */
    [COMPETENCY_ITEM.InterpersonalInfluence.ID]: {
      ...COMPETENCY_ITEM.InterpersonalInfluence,
      Options: [
        {
          Value: 1,
          Name: "相手に干渉しない",
          Help: COMPETENCY_ITEM.InterpersonalInfluence.PointLowText,
        },
        {
          Value: 2,
          Name: "相手に影響を与える",
          Help: COMPETENCY_ITEM.InterpersonalInfluence.PointHighText,
        },
      ],
    },
    /** 調整力 */
    [COMPETENCY_ITEM.Coordination.ID]: {
      ...COMPETENCY_ITEM.Coordination,
      Options: [
        {
          Value: 1,
          Name: "周囲との調整を避ける",
          Help: COMPETENCY_ITEM.Coordination.PointLowText,
        },
        {
          Value: 2,
          Name: "周囲との調整が得意",
          Help: COMPETENCY_ITEM.Coordination.PointHighText,
        },
      ],
    },
    /** 決断力 */
    [COMPETENCY_ITEM.Decisiveness.ID]: {
      ...COMPETENCY_ITEM.Decisiveness,
      Options: [
        {
          Value: 1,
          Name: "周囲の指示を受ける",
          Help: COMPETENCY_ITEM.Decisiveness.PointLowText,
        },
        {
          Value: 2,
          Name: "自分で決断する",
          Help: COMPETENCY_ITEM.Decisiveness.PointHighText,
        },
      ],
    },
    /** 活力 */
    [COMPETENCY_ITEM.Vitality.ID]: {
      ...COMPETENCY_ITEM.Vitality,
      Options: [
        {
          Value: 1,
          Name: "マイペースに取り組む",
          Help: COMPETENCY_ITEM.Vitality.PointLowText,
        },
        {
          Value: 2,
          Name: "エネルギッシュに取り組む",
          Help: COMPETENCY_ITEM.Vitality.PointHighText,
        },
      ],
    },
    /** 粘り強さ */
    [COMPETENCY_ITEM.Perseverance.ID]: {
      ...COMPETENCY_ITEM.Perseverance,
      Options: [
        {
          Value: 1,
          Name: "より簡単な問題を優先する",
          Help: COMPETENCY_ITEM.Perseverance.PointLowText,
        },
        {
          Value: 2,
          Name: "困難な問題に粘り強く取り組む",
          Help: COMPETENCY_ITEM.Perseverance.PointHighText,
        },
      ],
    },
    /** 一点集中 */
    [COMPETENCY_ITEM.Focus.ID]: {
      ...COMPETENCY_ITEM.Focus,
      Options: [
        {
          Value: 1,
          Name: "マルチタスク型",
          Help: COMPETENCY_ITEM.Focus.PointLowText,
        },
        {
          Value: 2,
          Name: "一点集中型",
          Help: COMPETENCY_ITEM.Focus.PointHighText,
        },
      ],
    },
    /** 継続力 */
    [COMPETENCY_ITEM.Continuity.ID]: {
      ...COMPETENCY_ITEM.Continuity,
      Options: [
        {
          Value: 1,
          Name: "状況に応じて目標を変えて取り組む",
          Help: COMPETENCY_ITEM.Continuity.PointLowText,
        },
        {
          Value: 2,
          Name: "一つの目標に向けて努力を継続できる",
          Help: COMPETENCY_ITEM.Continuity.PointHighText,
        },
      ],
    },
    /** プレッシャーへの耐性 */
    [COMPETENCY_ITEM.PressureTolerance.ID]: {
      ...COMPETENCY_ITEM.PressureTolerance,
      Options: [
        {
          Value: 1,
          Name: "プレッシャーを避ける",
          Help: COMPETENCY_ITEM.PressureTolerance.PointLowText,
        },
        {
          Value: 2,
          Name: "プレッシャーに強い",
          Help: COMPETENCY_ITEM.PressureTolerance.PointHighText,
        },
      ],
    },
    /** 対応力 */
    [COMPETENCY_ITEM.Adaptability.ID]: {
      ...COMPETENCY_ITEM.Adaptability,
      Options: [
        {
          Value: 1,
          Name: "決まったやり方で取り組む",
          Help: COMPETENCY_ITEM.Adaptability.PointLowText,
        },
        {
          Value: 2,
          Name: "臨機応変に取り組む",
          Help: COMPETENCY_ITEM.Adaptability.PointHighText,
        },
      ],
    },
    /** 人あたり */
    [COMPETENCY_ITEM.Sociability.ID]: {
      ...COMPETENCY_ITEM.Sociability,
      Options: [
        {
          Value: 1,
          Name: "自分の意見を主張する",
          Help: COMPETENCY_ITEM.Sociability.PointLowText,
        },
        {
          Value: 2,
          Name: "相手の意見を尊重する",
          Help: COMPETENCY_ITEM.Sociability.PointHighText,
        },
      ],
    },
    /** チームワーク */
    [COMPETENCY_ITEM.Teamwork.ID]: {
      ...COMPETENCY_ITEM.Teamwork,
      Options: [
        {
          Value: 1,
          Name: "単独で仕事に取り組む",
          Help: COMPETENCY_ITEM.Teamwork.PointLowText,
        },
        {
          Value: 2,
          Name: "チームにうまく溶け込む",
          Help: COMPETENCY_ITEM.Teamwork.PointHighText,
        },
      ],
    },
    /** 人間関係の構築 */
    [COMPETENCY_ITEM.RelationshipBuilding.ID]: {
      ...COMPETENCY_ITEM.RelationshipBuilding,
      Options: [
        {
          Value: 1,
          Name: "既存の人間関係を活かす",
          Help: COMPETENCY_ITEM.RelationshipBuilding.PointLowText,
        },
        {
          Value: 2,
          Name: "新たな人間関係を築く",
          Help: COMPETENCY_ITEM.RelationshipBuilding.PointHighText,
        },
      ],
    },
    /** 共感力 */
    [COMPETENCY_ITEM.Empathy.ID]: {
      ...COMPETENCY_ITEM.Empathy,
      Options: [
        {
          Value: 1,
          Name: "自分の都合を優先する",
          Help: COMPETENCY_ITEM.Empathy.PointLowText,
        },
        {
          Value: 2,
          Name: "周囲の事情に配慮する",
          Help: COMPETENCY_ITEM.Empathy.PointHighText,
        },
      ],
    },
    /** 創造性 */
    [COMPETENCY_ITEM.Creativity.ID]: {
      ...COMPETENCY_ITEM.Creativity,
      Options: [
        {
          Value: 1,
          Name: "すでにある方法を重視する",
          Help: COMPETENCY_ITEM.Creativity.PointLowText,
        },
        {
          Value: 2,
          Name: "新しい発想を取り入れる",
          Help: COMPETENCY_ITEM.Creativity.PointHighText,
        },
      ],
    },
    /** 問題解決力 */
    [COMPETENCY_ITEM.ProblemSolving.ID]: {
      ...COMPETENCY_ITEM.ProblemSolving,
      Options: [
        {
          Value: 1,
          Name: "問題意識を持たずに目の前の業務に取り組む",
          Help: COMPETENCY_ITEM.ProblemSolving.PointLowText,
        },
        {
          Value: 2,
          Name: "自ら問題を見つけて解決に取り組む",
          Help: COMPETENCY_ITEM.ProblemSolving.PointHighText,
        },
      ],
    },
    /** 計画性 */
    [COMPETENCY_ITEM.Planning.ID]: {
      ...COMPETENCY_ITEM.Planning,
      Options: [
        {
          Value: 1,
          Name: "その場で考えて進める",
          Help: COMPETENCY_ITEM.Planning.PointLowText,
        },
        {
          Value: 2,
          Name: "計画的に進める",
          Help: COMPETENCY_ITEM.Planning.PointHighText,
        },
      ],
    },
    /** 分析力 */
    [COMPETENCY_ITEM.AnalyticalAbility.ID]: {
      ...COMPETENCY_ITEM.AnalyticalAbility,
      Options: [
        {
          Value: 1,
          Name: "分析が不要な業務が得意",
          Help: COMPETENCY_ITEM.AnalyticalAbility.PointLowText,
        },
        {
          Value: 2,
          Name: "高度な分析が得意",
          Help: COMPETENCY_ITEM.AnalyticalAbility.PointHighText,
        },
      ],
    },
    /** 概念化 */
    [COMPETENCY_ITEM.Conceptualization.ID]: {
      ...COMPETENCY_ITEM.Conceptualization,
      Options: [
        {
          Value: 1,
          Name: "具体的でわかりやすい業務が得意",
          Help: COMPETENCY_ITEM.Conceptualization.PointLowText,
        },
        {
          Value: 2,
          Name: "抽象的な物事を体系的に整理できる",
          Help: COMPETENCY_ITEM.Conceptualization.PointHighText,
        },
      ],
    },
    /** 目標の立て方 */
    [COMPETENCY_ITEM.GoalSetting.ID]: {
      ...COMPETENCY_ITEM.GoalSetting,
      Options: [
        {
          Value: 1,
          Name: "手堅い目標を立てて安定的に活動する",
          Help: COMPETENCY_ITEM.GoalSetting.PointLowText,
        },
        {
          Value: 2,
          Name: "高い目標を掲げて挑戦を続ける",
          Help: COMPETENCY_ITEM.GoalSetting.PointHighText,
        },
      ],
    },
    /** 自学 */
    [COMPETENCY_ITEM.SelfLearning.ID]: {
      ...COMPETENCY_ITEM.SelfLearning,
      Options: [
        {
          Value: 1,
          Name: "教えてもらって学ぶ",
          Help: COMPETENCY_ITEM.SelfLearning.PointLowText,
        },
        {
          Value: 2,
          Name: "主体的に学ぶ",
          Help: COMPETENCY_ITEM.SelfLearning.PointHighText,
        },
      ],
    },
    /** 不確実性な状況 */
    [COMPETENCY_ITEM.UncertainSituations.ID]: {
      ...COMPETENCY_ITEM.UncertainSituations,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.UncertainSituations.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.UncertainSituations.PointHighText,
        },
      ],
    },
    /** 急な変化への対応 */
    [COMPETENCY_ITEM.ResponseToSuddenChanges.ID]: {
      ...COMPETENCY_ITEM.ResponseToSuddenChanges,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.ResponseToSuddenChanges.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.ResponseToSuddenChanges.PointHighText,
        },
      ],
    },
    /** ハードワーク */
    [COMPETENCY_ITEM.HardWork.ID]: {
      ...COMPETENCY_ITEM.HardWork,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.HardWork.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.HardWork.PointHighText,
        },
      ],
    },
    /** 計画性のなさ */
    [COMPETENCY_ITEM.LackOfPlanning.ID]: {
      ...COMPETENCY_ITEM.LackOfPlanning,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.LackOfPlanning.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.LackOfPlanning.PointHighText,
        },
      ],
    },
    /** 厳しい管理 */
    [COMPETENCY_ITEM.StrictManagement.ID]: {
      ...COMPETENCY_ITEM.StrictManagement,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.StrictManagement.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.StrictManagement.PointHighText,
        },
      ],
    },
    /** 評価の欠如 */
    [COMPETENCY_ITEM.LackOfEvaluation.ID]: {
      ...COMPETENCY_ITEM.LackOfEvaluation,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.LackOfEvaluation.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.LackOfEvaluation.PointHighText,
        },
      ],
    },
    /** 主体性が発揮できない */
    [COMPETENCY_ITEM.InabilityToExerciseInitiative.ID]: {
      ...COMPETENCY_ITEM.InabilityToExerciseInitiative,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.InabilityToExerciseInitiative.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.InabilityToExerciseInitiative.PointHighText,
        },
      ],
    },
    /** 意思決定に関与できない */
    [COMPETENCY_ITEM.ExclusionFromDecisionMaking.ID]: {
      ...COMPETENCY_ITEM.ExclusionFromDecisionMaking,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.ExclusionFromDecisionMaking.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.ExclusionFromDecisionMaking.PointHighText,
        },
      ],
    },
    /** 要求水準が低い */
    [COMPETENCY_ITEM.LowStandards.ID]: {
      ...COMPETENCY_ITEM.LowStandards,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.LowStandards.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.LowStandards.PointHighText,
        },
      ],
    },
    /** 高度な分析 */
    [COMPETENCY_ITEM.HighAnalysis.ID]: {
      ...COMPETENCY_ITEM.HighAnalysis,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.HighAnalysis.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.HighAnalysis.PointHighText,
        },
      ],
    },
    /** 学習機会の不足 */
    [COMPETENCY_ITEM.LackOfLearningOpportunities.ID]: {
      ...COMPETENCY_ITEM.LackOfLearningOpportunities,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.LackOfLearningOpportunities.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.LackOfLearningOpportunities.PointHighText,
        },
      ],
    },
    /** 前例踏襲 */
    [COMPETENCY_ITEM.FollowingPrecedents.ID]: {
      ...COMPETENCY_ITEM.FollowingPrecedents,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.FollowingPrecedents.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.FollowingPrecedents.PointHighText,
        },
      ],
    },
    /** 定型業務 */
    [COMPETENCY_ITEM.RoutineWork.ID]: {
      ...COMPETENCY_ITEM.RoutineWork,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.RoutineWork.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.RoutineWork.PointHighText,
        },
      ],
    },
    /** 困難な決断 */
    [COMPETENCY_ITEM.DifficultDecisions.ID]: {
      ...COMPETENCY_ITEM.DifficultDecisions,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.DifficultDecisions.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.DifficultDecisions.PointHighText,
        },
      ],
    },
    /** 交渉業務 */
    [COMPETENCY_ITEM.NegotiationTasks.ID]: {
      ...COMPETENCY_ITEM.NegotiationTasks,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.NegotiationTasks.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.NegotiationTasks.PointHighText,
        },
      ],
    },
    /** 合意形成 */
    [COMPETENCY_ITEM.ConsensusBuilding.ID]: {
      ...COMPETENCY_ITEM.ConsensusBuilding,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.ConsensusBuilding.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.ConsensusBuilding.PointHighText,
        },
      ],
    },
    /** 周囲との対立 */
    [COMPETENCY_ITEM.ConflictWithOthers.ID]: {
      ...COMPETENCY_ITEM.ConflictWithOthers,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.ConflictWithOthers.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.ConflictWithOthers.PointHighText,
        },
      ],
    },
    /** ドライな職場 */
    [COMPETENCY_ITEM.DryWorkplace.ID]: {
      ...COMPETENCY_ITEM.DryWorkplace,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.DryWorkplace.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.DryWorkplace.PointHighText,
        },
      ],
    },
    /** 板挟み状態 */
    [COMPETENCY_ITEM.CaughtInTheMiddle.ID]: {
      ...COMPETENCY_ITEM.CaughtInTheMiddle,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.CaughtInTheMiddle.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.CaughtInTheMiddle.PointHighText,
        },
      ],
    },
    /** 共同業務 */
    [COMPETENCY_ITEM.CollaborativeWork.ID]: {
      ...COMPETENCY_ITEM.CollaborativeWork,
      Options: [
        {
          Value: 1,
          Name: "ストレスを感じにくい",
          Help: COMPETENCY_ITEM.CollaborativeWork.PointLowText,
        },
        {
          Value: 2,
          Name: "ストレスを感じやすい",
          Help: COMPETENCY_ITEM.CollaborativeWork.PointHighText,
        },
      ],
    },
    // 「孤独な業務」は結果表示しない（「共同業務」に統合。ミイダスラップでは引き続き使用する。）
    /** 孤独な業務 */
    // TODO:renewcompe いつも邪魔なので後で消します。ミイダスラップでのみ使用しているため、ミイダスラップ用の定数を作ります。
    [COMPETENCY_ITEM.SolitaryWork.ID]: {
      ...COMPETENCY_ITEM.SolitaryWork,
      Options: [
        { Value: 1, Name: "", Help: "" },
        { Value: 2, Name: "", Help: "" },
      ],
    },
    /** 指示型 */
    [COMPETENCY_ITEM.Directive.ID]: {
      ...COMPETENCY_ITEM.Directive,
      // 上司・部下としての傾向のHelpは、選択肢を問わず共通のDescriptionを使用する
      Options: [
        {
          Value: 1,
          Name: "指示型ではない",
          Help: COMPETENCY_ITEM.Directive.Description,
        },
        {
          Value: 2,
          Name: "指示型である",
          Help: COMPETENCY_ITEM.Directive.Description,
        },
      ],
    },
    /** 委任型 */
    [COMPETENCY_ITEM.Delegation.ID]: {
      ...COMPETENCY_ITEM.Delegation,
      Options: [
        {
          Value: 1,
          Name: "委任型ではない",
          Help: COMPETENCY_ITEM.Delegation.Description,
        },
        {
          Value: 2,
          Name: "委任型である",
          Help: COMPETENCY_ITEM.Delegation.Description,
        },
      ],
    },
    /** 傾聴型 */
    [COMPETENCY_ITEM.Listening.ID]: {
      ...COMPETENCY_ITEM.Listening,
      Options: [
        {
          Value: 1,
          Name: "傾聴型ではない",
          Help: COMPETENCY_ITEM.Listening.Description,
        },
        {
          Value: 2,
          Name: "傾聴型である",
          Help: COMPETENCY_ITEM.Listening.Description,
        },
      ],
    },
    /** 対話型 */
    [COMPETENCY_ITEM.Dialogue.ID]: {
      ...COMPETENCY_ITEM.Dialogue,
      Options: [
        {
          Value: 1,
          Name: "対話型ではない",
          Help: COMPETENCY_ITEM.Dialogue.Description,
        },
        {
          Value: 2,
          Name: "対話型である",
          Help: COMPETENCY_ITEM.Dialogue.Description,
        },
      ],
    },
    /** 交渉型 */
    [COMPETENCY_ITEM.Negotiation.ID]: {
      ...COMPETENCY_ITEM.Negotiation,
      Options: [
        {
          Value: 1,
          Name: "交渉型ではない",
          Help: COMPETENCY_ITEM.Negotiation.Description,
        },
        {
          Value: 2,
          Name: "交渉型である",
          Help: COMPETENCY_ITEM.Negotiation.Description,
        },
      ],
    },
    /** 従順型 */
    [COMPETENCY_ITEM.Obedient.ID]: {
      ...COMPETENCY_ITEM.Obedient,
      Options: [
        {
          Value: 1,
          Name: "従順型ではない",
          Help: COMPETENCY_ITEM.Obedient.Description,
        },
        {
          Value: 2,
          Name: "従順型である",
          Help: COMPETENCY_ITEM.Obedient.Description,
        },
      ],
    },
    /** 自律型 */
    [COMPETENCY_ITEM.Autonomous.ID]: {
      ...COMPETENCY_ITEM.Autonomous,
      Options: [
        {
          Value: 1,
          Name: "自律型ではない",
          Help: COMPETENCY_ITEM.Autonomous.Description,
        },
        {
          Value: 2,
          Name: "自律型である",
          Help: COMPETENCY_ITEM.Autonomous.Description,
        },
      ],
    },
    /** 協調型 */
    [COMPETENCY_ITEM.Cooperative.ID]: {
      ...COMPETENCY_ITEM.Cooperative,
      Options: [
        {
          Value: 1,
          Name: "協調型ではない",
          Help: COMPETENCY_ITEM.Cooperative.Description,
        },
        {
          Value: 2,
          Name: "協調型である",
          Help: COMPETENCY_ITEM.Cooperative.Description,
        },
      ],
    },
    /** 提案型 */
    [COMPETENCY_ITEM.Proactive.ID]: {
      ...COMPETENCY_ITEM.Proactive,
      Options: [
        {
          Value: 1,
          Name: "提案型ではない",
          Help: COMPETENCY_ITEM.Proactive.Description,
        },
        {
          Value: 2,
          Name: "提案型である",
          Help: COMPETENCY_ITEM.Proactive.Description,
        },
      ],
    },
    /** 主張型 */
    [COMPETENCY_ITEM.Assertive.ID]: {
      ...COMPETENCY_ITEM.Assertive,
      Options: [
        {
          Value: 1,
          Name: "主張型ではない",
          Help: COMPETENCY_ITEM.Assertive.Description,
        },
        {
          Value: 2,
          Name: "主張型である",
          Help: COMPETENCY_ITEM.Assertive.Description,
        },
      ],
    },
  };

// 勤務地省略時の最大限の表示数
export const WORK_ADDRESS_OMITTED_MAX_DISPLAY_COUNT = 3;

// 子ノードの表示を省略し「続きを読む」ボタンを表示する高さ
export const READ_MORE_SECTION_OMITTED_HEIGHT = {
  POSITION_PR: 250, // 求人のポイント
  COMPANY_PR: 250, // 企業の特徴
  JOB_TYPE: 250, // 仕事内容
  SPOT_JOB_REQUEST: 250, // 業務委託（スポット）依頼内容
  COMMISSION_BUSINESS_DESCRIPTION: 250, // 業務委託（完全歩合制）業務内容
  COMMISSION_FEE: 250, // 業務委託（完全歩合制）報酬
  OTHER_JOB_SPECIFIED: 100, // その他の特徴
  BUSINESS_OVERVIEW: 250, // 事業の特徴
  BUSINESS_SPECIFIED: 100, // 事業の詳細
  CULTURE_AND_HR_EVALUATION: 220, // 社風・評価基準の特徴
  CAREER: 100, // キャリア制度
  EMPLOYEE_ATTRIBUTES: 100, // 社員属性
  INDUSTRY_RESEARCH: 100, // 業界研究
} as const;

// 求人一覧の1ページの件数
export const POSITION_LIMIT = 20;

// 業務委託求人のアピールポイント: 業務内容のマスター
export const OUTSOURCING_APPEAL_WORK_TYPE_ID_WORK = 0; // 実務
export const OUTSOURCING_APPEAL_WORK_TYPE_ID_CONSULTANT = 1; // 業務の支援
export const OUTSOURCING_APPEAL_WORK_TYPE_ID_RESEARCH = 2; // 情報収集
export const OUTSOURCING_APPEAL_WORK_TYPE_MASTER = [
  {
    // マスターとしては用意するが、表示されない
    ID: OUTSOURCING_APPEAL_WORK_TYPE_ID_WORK,
    Name: "実務",
  },
  {
    ID: OUTSOURCING_APPEAL_WORK_TYPE_ID_CONSULTANT,
    Name: "業務の支援（コンサルタント・アドバイザーなど）",
  },
  {
    ID: OUTSOURCING_APPEAL_WORK_TYPE_ID_RESEARCH,
    Name: "情報収集（調査・インタビューなど）",
  },
] as const;

// 業務内容アピールポイントのSVGアイコン表示用マッピング
export const APPEAL_WORK_TYPE_ID_ICON_MAP = {
  [OUTSOURCING_APPEAL_WORK_TYPE_ID_CONSULTANT]: ICON.OFFER.WORKTYPE_CONSULTING,
  [OUTSOURCING_APPEAL_WORK_TYPE_ID_RESEARCH]: ICON.OFFER.WORKTYPE_RESEARCH,
} as const;

// トレイトの特殊表示条件
export const EXCEPTION_TRAIT_OPTION = {
  // 契約内容 該当なし
  PTJ_DEVELOPMENT_PROCESS: -1,
  // 労働環境の特徴 該当なし
  PTX_WORKING_ENVIRONMENT: -1,
  // 在宅勤務 なし
  PTX_REMOTE_WORK: 1,
} as const;

/**
 * 役職
 */
export const POST = {
  NONE: {
    ID: 1,
    Name: "役職なし",
  },
  LEADER: {
    ID: 2,
    Name: "係長／リーダークラス",
  },
  MANAGER: {
    ID: 3,
    Name: "課長／マネージャークラス",
  },
  GENERAL_MANAGER: {
    ID: 4,
    Name: "部長／ゼネラルマネージャークラス",
  },
  EXECUTIVE_OFFICER: {
    ID: 5,
    Name: "役員クラス",
  },
  CEO: {
    ID: 6,
    Name: "代表クラス",
  },
} as const;

// 募集条件一致率
export const TARGET_MATCH_A = 1;

// 募集条件一致率
const TARGET_MATCH = {
  [TARGET_MATCH_A]: "A",
  2: "B",
  3: "C",
  4: "D",
  5: "E",
} as const;

// 活躍可能性
const COMPETENCY_MATCH = {
  1: "A",
  2: "B",
  3: "C",
} as const;

/**
 * 募集条件一致率・活躍可能性
 */
export const MATCH_RANK = {
  TARGET_MATCH,
  COMPETENCY_MATCH,

  // 募集条件一致率の表示用ラベルを取得する
  getTargetMatchRankLabel: (
    v: keyof typeof TARGET_MATCH | null | 0,
  ): string => {
    return v ? TARGET_MATCH[v] : "?";
  },

  // 活躍可能性の表示用ラベルを取得する
  getCompetencyMatchRankLabel: (
    v: keyof typeof COMPETENCY_MATCH | null | 0,
  ): string => {
    return v ? COMPETENCY_MATCH[v] : "?";
  },
} as const;

// 公開状況
export const PUBLISH_STATUS = {
  PRIVATE: 0, // 非公開
  PUBLISHED: 1, // 公開
} as const;

// 応募タイプ
export const APPLICATION_COMPLETE_APPLICATION_TYPE = {
  APPLICATION: "APPLICATION",
  MEETING: "MEETING",
  QUESTION: "QUESTION",
  NONE: "NONE", // 未指定（初期値）
} as const;

// 求人画像: メイン/サブ画像のタイプ
export const POSITION_IMAGE_DISPLAY_TYPE = {
  MAIN: 1,
  SUB: 2,
} as const;

// 求人画像の最大数
export const MAX_POSITION_IMAGES_COUNT = 3;

// 求人ラベルの表示タイプ
export const POSITION_LABEL_DISPLAY_TYPE = {
  SUMMARY: "POSITION_SUMMARY",
  DETAIL: "POSITION_DETAIL",
  CARD: "POSITION_CARD",
} as const;
