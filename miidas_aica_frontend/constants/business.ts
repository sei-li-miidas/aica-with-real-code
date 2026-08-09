/**
 * トレイトオプション一覧
 *
 * トレイト表示画面において、Viewの組み立てやTraitレコードとのマッピングに用いる
 * （AppealなどはTraitレコードに含まれるので、すべてTraitレコードに含めて定数はIDだけにしてもいいかもしれない）
 * IDのプレフィックス（ptx_など）について
 * ct：企業特徴、pt:ポジション特徴、bt:事業内容
 * 共通ー＞x
 * 業種ごとのものー＞i
 * 職種ごとのものー＞j
 *
 *  ID   : トレイトID
 *  Name : トレイト項目名
 *  Help : トレイト項目のヘルプ
 */
export const TRAITS = {
  BTI_CAR_PARTS_TIER: {
    ID: "bti_car_parts_tier",
    Name: "Tier",
  },
  BTI_CONTRACT_COMPANY__CLIENT_RESIDENT: {
    ID: "bti_contract_company__client_resident",
    Name: "客先常駐",
  },
  BTI_CONTRACT_COMPANY__PROFIT_SOURCE: {
    ID: "bti_contract_company__profit_source",
    Name: "主な収益源",
  },
  BTI_CONTRACT_COMPANY__PROJECT_TERM: {
    ID: "bti_contract_company__project_term",
    Name: "プロジェクト期間",
  },
  BTI_CONTRACT_COMPANY__RESIDENT_TYPE: {
    ID: "bti_contract_company__resident_type",
    Name: "常駐形態",
  },
  BTI_MEDICAL_ADVANTAGE_FIELD: {
    ID: "bti_medical_advantage_field",
    Name: "得意領域",
  },
  BTI_SI__ADVANTAGE_INDUSTRY: {
    ID: "bti_si__advantage_industry",
    Name: "得意領域（SIer）",
  },
  BTI_SI__TYPE: {
    ID: "bti_si__type",
    Name: "SI種別",
  },
  BTX_BUSINESS_INDUSTRY: {
    ID: "btx_business_industry",
    Name: "事業内容",
  },
  BTX_BUSINESS_TEXT: {
    ID: "btx_business_text",
    Name: "事業内容の詳細",
  },
  BTX_DECISION_TYPE: {
    ID: "btx_decision_type",
    Name: "意思決定と裁量",
  },
  BTX_EMPLOYEE_AVERAGE_AGE: {
    ID: "btx_employee_average_age",
    Name: "平均年齢",
  },
  BTX_EMPLOYEE_CHARACTER: {
    ID: "btx_employee_character",
    Name: "組織・社員の特徴",
  },
  BTX_EMPLOYEE_FOREIGN_NATIONALITY_RATE: {
    ID: "btx_employee_foreign_nationality_rate",
    Name: "外国籍社員比率",
  },
  BTX_EMPLOYEE_MID_CAREER_RATE: {
    ID: "btx_employee_mid_career_rate",
    Name: "中途入社社員比率",
  },
  BTX_EMPLOYEE_QTY: {
    ID: "btx_employee_qty",
    Name: "事業の規模",
  },
  BTX_EMPLOYEE_WOMAN_RATE: {
    ID: "btx_employee_woman_rate",
    Name: "女性社員比率",
  },
  BTX_FOREIGN_NATIONALITY_RECRUITING: {
    ID: "btx_foreign_nationality_recruiting",
    Name: "外国籍社員積極採用",
  },
  BTX_SALES_SCALE: {
    ID: "btx_sales_scale",
    Name: "事業の売上規模",
  },
  BTX_YEARS_OF_ESTABLISHMENT: {
    ID: "btx_years_of_establishment",
    Name: "事業の設立",
  },
} as const;

// トレイトオプションのヘルプ一覧
export const TRAIT_OPTION_HELPS = {
  // 組織・社員の特長
  btx_employee_character: {
    6: {
      left: {
        title: "ITを活用しない",
        text: "紙文化（決裁資料、会議資料など）",
      },
      right: {
        title: "ITを活用している",
        text: "チャット使用、オンライン会議など",
      },
    },
    9: {
      left: {
        title: "社内イベントが多い",
        text: "運動会、合宿、花見など",
      },
    },
  },
} as const;

// トレイトの特殊非表示条件
export const EXCEPTION_HIDDEN_TRAIT_OPTION = {
  // SI種別 該当なし
  BTI_SI__TYPE: -1,
  // 得意領域（SIer） 該当なし
  BTI_SI__ADVANTAGE_INDUSTRY: -1,
  // 得意領域（メディカル） 該当なし
  BTI_MEDICAL_ADVANTAGE_FIELD: -1,
  // メーカー（自動車部品）Tier該当なし
  BTI_CAR_PARTS_TIER: -1,
  // 主な収益源 非公開
  BTI_CONTRACT_COMPANY__PROFIT_SOURCE: 7,
  // プロジェクト期間 非公開
  BTI_CONTRACT_COMPANY__PROJECT_TERM: 6,
  // 客先常駐 非公開
  BTI_CONTRACT_COMPANY__CLIENT_RESIDENT: 5,
  // 常駐形態 非公開
  BTI_CONTRACT_COMPANY__RESIDENT_TYPE: 5,
} as const;
