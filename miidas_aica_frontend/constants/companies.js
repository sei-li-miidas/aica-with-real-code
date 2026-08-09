/**
 * トレイトオプション一覧
 *
 * トレイト表示画面において、Viewの組み立てやTraitレコードとのマッピングに用いる
 * （AppealなどはTraitレコードに含まれるので、すべてTraitレコードに含めて定数はIDだけにしてもいいかもしれない）
 *
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
/*
  NOTE: ポジション詳細はトレイトではなくなったが、2022/02/04現在企業検索がまだトレイトである。(後にこっちもトレイトじゃなくなる予定)
  二重に同じ項目の定数を持ちたくないため、トレイト以外となったポジション詳細からも、トレイト名称のこの定数を呼んでいる
 */
export const TRAITS = {
  // 企業概要
  CTX_PRESIDENT_NAME: {
    ID: "ctx_president_name",
    Name: "代表者名",
  },
  CTX_WEBSITE: {
    ID: "ctx_website",
    Name: "企業サイトURL",
  },
  CTX_IS_PROFIT_COMPANY: {
    ID: "ctx_is_profit_company",
    Name: "法人種別",
  },
  CTX_EMPLOYEE_QTY: {
    ID: "ctx_employee_qty",
    Name: "企業規模",
  },
  CTX_YEARS_OF_ESTABLISHMENT: {
    ID: "ctx_years_of_establishment",
    Name: "設立",
  },
  CTX_CAPITAL_TYPE: {
    ID: "ctx_capital_type",
    Name: "資本区分",
  },
  CTX_SALES_SCALE: {
    ID: "ctx_sales_scale",
    Name: "売上規模",
  },
  CTX_INTRODUCTION: {
    ID: "ctx_introduction",
    Name: "企業紹介コメント",
  },
  CTX_APPEAL_POINT: {
    ID: "ctx_appeal_point",
    Name: "当社のアピールポイント",
  },
  CTX_SALES_OVERSEAS_RATE: {
    ID: "ctx_sales_overseas_rate",
    Name: "海外売上比率",
  },
  // 休日休暇
  CTX_YEAR_HOLIDAYS: {
    ID: "ctx_year_holidays",
    Name: "年間休日",
  },
  CTX_VACATIONS: {
    ID: "ctx_vacations",
    Name: "福利厚生（休日休暇）",
  },
  CTX_PAID_HOLIDAY_USE_RATE: {
    ID: "ctx_paid_holiday_use_rate",
    Name: "有給休暇取得率",
    Help: {
      title: "有給休暇取得率",
      text: "1年間にもらえる有給休暇のうち、実際どれぐらい取得したのかを示す数字。10日もらった人が5日取得したら「50%」となる。",
    },
  },
  // キャリア
  CTX_TRAINING_SYSTEM_EXISTS: {
    ID: "ctx_training_system_exists",
    Name: "研修制度",
  },
  CTX_TRAINING_SYSTEM_TEXT: {
    ID: "ctx_training_system_text",
    Name: "研修内容",
  },
  CTX_JOB_ROTATION_EXISTS: {
    ID: "ctx_job_rotation_exists",
    Name: "社員の成長のための定期的な部署異動（ジョブローテーション）",
    Help: {
      title: "社員の成長のための定期的な部署異動（ジョブローテーション）",
      text: "社員の能力向上を目的とし、戦略的な部署・職種の異動を行う制度",
    },
  },
  CTX_CHANGE_DEPARTMENT_REQUEST: {
    ID: "ctx_change_department_request",
    Name: "異動希望",
    Help: {
      title: "異動希望",
      text: "社員が異動希望を提出し、希望先の部署で承認されれば、必ず異動できる制度",
    },
  },
  // 福利厚生
  CTX_WELFARE__INSURANCE: {
    ID: "ctx_welfare__insurance",
    Name: "社会保険",
  },
  CTX_WELFARE__BENEFIT: {
    ID: "ctx_welfare__benefit",
    Name: "福利厚生（待遇）",
  },
  CTX_WELFARE__ACHIEVEMENT: {
    ID: "ctx_welfare__achievement",
    Name: "実績のある福利厚生",
  },
  CTX_WELFARE__POPULAR: {
    ID: "ctx_welfare__popular",
    Name: "人気の福利厚生",
  },
  CTX_WELFARE__OTHER: {
    ID: "ctx_welfare__other",
    Name: "その他福利厚生",
  },
  // 採用関連
  CTX_OTHER: {
    ID: "ctx_other",
    Name: "その他企業特徴",
  },
  // 業種別企業特徴
  // その他
  CTX_PR: {
    ID: "ctx_pr",
    Name: "企業PR",
  },
  CTX_SIDE_BUSINESS: {
    ID: "ctx_side_business",
    Name: "副業",
  },
  CTX_SIDE_BUSINESS_CONDITION: {
    ID: "ctx_side_business_condition",
    Name: "副業の条件",
  },
  // 社員属性
  CTX_HR_EVALUATION__WOMAN_MANAGER_RATE: {
    ID: "ctx_hr_evaluation__woman_manager_rate",
    Name: "女性管理職比率",
  },
  CTX_HR_EVALUATION__20S_MANAGER_RATE: {
    ID: "ctx_hr_evaluation__20s_manager_rate",
    Name: "20代管理職",
  },
};

// トレイトオプションのヘルプ一覧
export const TRAIT_OPTION_HELPS = {
  // 資本区分
  ctx_capital_type: {
    3: {
      title: "オーナー企業・ファミリー企業",
      text: "1/2以上の株式をオーナーまたはオーナー一族で保有",
    },
    4: {
      title: "外資系企業",
      text: "1/3以上の株式が外国投資家が保有",
    },
  },
  // 当社のアピールポイント
  ctx_appeal_point: {
    1: {
      title: "安定した事業",
      text: "浮き沈みが少ない安定した業界",
    },
    2: {
      title: "成長性のある事業",
      text: "今後伸びる業界、産業、事業である",
    },
    4: {
      title: "福利厚生に自信",
      text: "退職金、家賃補助など福利厚生が充実している",
    },
    5: {
      title: "評価制度に自信",
      text: "わかりやすく、公正な、納得度の高い評価制度",
    },
    6: {
      title: "社員の定着率",
      text: "退職率が低い",
    },
    7: {
      title: "働きやすい",
      text: "残業少ない、休日多い、有給取得しやすいなど",
    },
    8: {
      title: "女性が働きやすい",
      text: "①産休・育休取得実績、介護休暇取得実績がある\n②時短勤務、在宅勤務ができる\n③女性管理職比率が高い\n④託児所がある\nなど",
    },
    11: {
      title: "スタートアップ",
      text: "スタートアップは主に短期間でのEXITを目的にしている",
    },
    12: {
      title: "ベンチャー企業",
      text: "ベンチャー企業は中長期的に課題に取り組み、世の中の課題を解決を目指す",
    },
    13: {
      title: "理念経営",
      text: "経営理念やビジョンが社員に浸透しており、共感、一体感のある経営ができている",
    },
    14: {
      title: "チャレンジできる風土",
      text: "若くても裁量を与えられ、チャレンジできる",
    },
    15: {
      title: "オフィスに自信",
      text: "オフィスの設備、立地、清潔感、食堂など",
    },
  },
};

// ミイダス認定定数
export const CERTIFICATION_RANK = {
  NONE: 0,
  BRONZE: 1,
  SILVER: 2,
  GOLD: 3,
};

// トレイトの特殊非表示条件
export const EXCEPTION_HIDDEN_TRAIT_OPTION = {
  // 法人種別 営利団体
  CTX_IS_PROFIT_COMPANY: 1,
  // 異動希望申請制度 なし
  CTX_CHANGE_DEPARTMENT_REQUEST: 2,
  // 有給休暇取得率 不明
  CTX_PAID_HOLIDAY_USE_RATE: 4,

  // MultipleValueAndText 該当なし
  MULTIPLE_TRAIT: -1,
  // 海外売上比率 なし、10%未満
  CTX_SALES_OVERSEAS_RATE: [1, 2, 3],
};

// トレイトオプションの値
export const TRAIT_OPTION_VALUES = {
  // 副業
  CTX_SIDE_BUSINESS: {
    /** 副業NG */
    NG: 1,
    /** 副業OK（条件あり） */
    OK_WITH_RULE: 2,
    /** 副業OK（条件なし） */
    OK: 3,
  },
  // 年間休日
  CTX_YEAR_HOLIDAYS: {
    /** 120日未満 */
    UNDER_120: 1,
    /** 120日以上 */
    OVER_120: 2,
    /** 130日以上 */
    OVER_130: 3,
    /** 140日以上 */
    OVER_140: 4,
  },
};
