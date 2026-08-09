// マスタのキー一覧
export const MASTER_KEYS = {
  PREFECTURE: "Prefecture",
  CITY: "City",
  EMPLOYMENT_TYPE: "EmploymentType",
  EXP_COMPANY: "ExpCompany",
  EMPLOYEE_QTY: "EmployeeQty",
  SCHOOL_TYPE: "SchoolType",
  SCHOOL: "School",
  DEPARTMENT_TYPE: "DepartmentType",
  PROFESSIONAL_TRAINING_COLLEGE_CATEGORY: "ProfessionalTrainingCollegeCategory",
  LANG_LEVEL: "LangLevel",
  MANAGEMENT_PEOPLE_QTY: "ManagementPeopleQty",
} as const;

// 勤務先のエリアグループ
export const PREFECTURE = {
  // エリアグループ名
  AREA_GROUP: {
    10: "北海道・東北",
    11: "関東",
    12: "中部",
    13: "近畿",
    14: "中国・四国",
    15: "九州・沖縄",
  },
  // エリア→エリアグループの紐付け
  AREA_GROUP_MAPPING: {
    1: 10,
    2: 10,
    3: 11,
    4: 12,
    5: 13,
    6: 14,
    7: 14,
    8: 15,
  },
} as const;

// 希望勤務地に「海外」を追加するためのマスターデータ
// ※サーバでは使用せず、フロントでのみ使用するデータであり、
//  POSTする際は希望勤務地としてではなくOverseasFlgとしてリクエストパラメータに含める
export const WORK_OVERSEAS = {
  ID: 99,
  Name: "海外",
} as const;

// ポジション 契約形態
export const EMPLOYMENT_TYPE = {
  FULL_TIME: 1, // 正社員
  CONTRACT: 2, // 契約社員
  OFFICER: 3, // 役員
  OUTSOURCING: 4, // 業務委託
} as const;

// ポジション ストックオプション制度
export const STOCK_OPTION = {
  EXIST: 1, // あり
  NONE: 2, // なし
} as const;

// ポジション 固定残業代の有無
export const HAS_OVERTIME_SALARY = {
  EXIST: 1, // あり
  NONE: 2, // なし
} as const;

// 企業情報 レンジラジオタイプ
export const RANGE_RADIO = {
  // 組織・社員の特長
  btx_employee_character: {
    1: {
      groupKey: "（1）",
      labels: { left: "若手が活躍", right: "中堅・ベテランが活躍" },
    },
    2: {
      groupKey: "（2）",
      labels: { left: "挑戦的な社風", right: "堅実な社風" },
    },
    3: {
      groupKey: "（3）",
      labels: { left: "活気がある", right: "落ち着いている" },
    },
    4: {
      groupKey: "（4）",
      labels: { left: "上下関係がある", right: "上下関係がない" },
    },
    5: {
      groupKey: "（5）",
      labels: { left: "雰囲気が事務的", right: "雰囲気がアットホーム" },
    },
    6: {
      groupKey: "（6）",
      labels: { left: "ITを活用しない", right: "ITを活用している" },
    },
    7: {
      groupKey: "（7）",
      labels: { left: "体育会系", right: "文化系" },
    },
    8: {
      groupKey: "（8）",
      labels: { left: "仕事重視", right: "プライベート重視" },
    },
    9: {
      groupKey: "（9）",
      labels: { left: "社内イベントが多い", right: "社内イベントが少ない" },
    },
    10: {
      groupKey: "（10）",
      labels: { left: "上司との飲み会が多い", right: "上司との飲み会が少ない" },
    },
    11: {
      groupKey: "（11）",
      labels: { left: "同僚との飲み会が多い", right: "同僚との飲み会が少ない" },
    },
    12: {
      groupKey: "（12）",
      labels: {
        left: "企業理念が従業員に\n浸透している",
        right: "企業理念が従業員に\n浸透していない",
      },
    },
  },
  // 意思決定と裁量
  btx_decision_type: {
    1: {
      groupKey: "（1）",
      labels: { left: "経営陣の決定を重視", right: "現場の従業員の声を重視" },
    },
    2: {
      groupKey: "（2）",
      labels: { left: "規則を重視", right: "組織のバランスを重視" },
    },
    3: {
      groupKey: "（3）",
      labels: { left: "経営陣に裁量がある", right: "現場に裁量がある" },
    },
    4: {
      groupKey: "（4）",
      labels: {
        left: "仕事の進め方にルールがある",
        right: "自分のやり方で進められる",
      },
    },
  },
  // 評価基準の特徴
  ptx_hr_evaluation_type: {
    1: {
      groupKey: "Type1",
      labels: { left: "実力主義", right: "年功序列" },
    },
    2: {
      groupKey: "Type2",
      labels: { left: "長所を伸ばす", right: "短所を克服" },
    },
    3: {
      groupKey: "Type3",
      labels: { left: "結果や成果を評価", right: "やり方や過程を評価" },
    },
    4: {
      groupKey: "Type4",
      labels: { left: "個性を重視", right: "協調性を重視" },
    },
  },
} as const;

// 入社・退社年のSelectのoptions設定値
// 60年前から今年まで
const termYearOptions = Array.from(Array(61).keys())
  .map((i) => {
    const d = new Date();
    const year = d.getFullYear();
    const value = year - i;
    return {
      ID: value,
      Name: value,
    };
  })
  .reverse();
export const TERM_YEAR_OPTIONS = termYearOptions;

export const DRIVE_LICENCE_VALUE_FOR_RADIO_LIST = {
  FULL_DRIVER_LICENCE: 2,
  DRIVER_LICENCE: 1,
  NOT_DRIVER_LICENCE: 0,
} as const;
// 運転免許有無のマスタ
export const DRIVE_LICENCE = [
  {
    ID: DRIVE_LICENCE_VALUE_FOR_RADIO_LIST.DRIVER_LICENCE,
    Name: "持っている（AT車限定）",
  },
  {
    ID: DRIVE_LICENCE_VALUE_FOR_RADIO_LIST.FULL_DRIVER_LICENCE,
    Name: "持っている（MT車）",
  },
  {
    ID: DRIVE_LICENCE_VALUE_FOR_RADIO_LIST.NOT_DRIVER_LICENCE,
    Name: "免許を持っていない",
  },
] as const;

// 年齢の上限
export const MAX_AGE = 99;
// 年齢の下限
export const MIN_AGE = 15;
// 年齢の初期値
const DEFAULT_AGE = 30;

// 生年月の初期値
export const DEFAULT_BIRTHDAY = {
  get YEAR() {
    const d = new Date();
    const year = d.getFullYear();
    return year - DEFAULT_AGE;
  },
  MONTH: 1,
} as const;

// 生年月の年Selectのoptions設定値
export const BIRTH_YEAR_OPTIONS = Array.from(
  Array(MAX_AGE - MIN_AGE + 1).keys(),
)
  .map((i) => {
    const d = new Date();
    const year = d.getFullYear();
    const value = year - MIN_AGE - i;
    return {
      ID: value,
      Name: value,
    };
  })
  .reverse();

// 月Selectのoptions設定値(1, 2, 3, ..., 12)
export const MONTH_OPTIONS = Array.from(Array(12).keys()).map((i) => {
  const value = i + 1;
  return {
    ID: value,
    Name: value,
  };
});

// 日Selectのoptions設定値(1, 2, 3, ..., 31)
export const DAY_OPTIONS = Array.from(Array(31).keys()).map((i) => {
  const value = i + 1;
  return {
    ID: value,
    Name: value,
  };
});

// 卒業年のSelectのoptions設定値
// 100年前から今年まで
export const GRADUATION_YEAR_OPTIONS = Array.from(Array(100).keys())
  .map((i) => {
    const d = new Date();
    const year = d.getFullYear();
    const value = year - i;
    return {
      ID: value,
      Name: value,
    };
  })
  .reverse();

// 職種・スキルの経験年数のID
export const EXP_TERM_IDS = {
  NO_EXPERIENCE: 1,
  LESS_THAN_A_YEAR: 2,
  MORE_THAN_TEN_YEARS: 12,
} as const;
