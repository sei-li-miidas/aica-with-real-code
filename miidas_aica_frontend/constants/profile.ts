export enum LocationType {
  RESIDENCE = "居住地",
  COMMUTING_AREAS = "通勤圏",
  WORK_LOCATION = "希望勤務地",
  FULL_REMOTE_WORK = "フルリモート",
}

// 希望勤務地最大都道府県数
export const MAX_WILL_WORK_ADDRESSES_PREFECTURES_COUNT: number = 5;
// 最大希望勤務地数
export const MAX_WILL_WORK_ADDRESSES_CITIES_COUNT: number = 40;
// 希望勤務地表示エリア表示できる件数（それ以上の場合スクロール）
export const WILL_WORK_ADDRESSES_CITIES_SCROLL_THRESHOLD: number = 6;
// 希望勤務地表示エリア最大高さ
export const WILL_WORK_ADDRESSES_CITIES_MAX_HEIGHT: string = "330px";
// 最大希望職種数
export const MAX_WILL_JOBTYPES_SMALLS_COUNT: number = 40;
// 希望職種表示エリア表示できる件数（それ以上の場合スクロール）
export const WILL_JOBTYPES_SMALLS_SCROLL_THRESHOLD: number = 6;
// 希望職種表示エリア最大高さ
export const WILL_JOBTYPES_SMALLS_MAX_HEIGHT: string = "330px";
// 入退社に登録可能なのは何年前までか
export const CAREER_MIN_JOIN_RETIRE_YEARS: number = 60; // 60年前まで
// 直近企業の最大年収
export const CAREER_MAX_INCOME: number = 9999; // 9,999万円まで
// 卒業に登録可能なのは何年前までか
export const EDUCATION_MIN_GRADUATION_YEAR: number = 100; // 100年前まで

// 言語オプション
export const LANGUAGES = [
  {
    ID: "91",
    Name: "日本語",
  },
  {
    ID: "92",
    Name: "英語",
  },
  {
    ID: "1",
    Name: "北京語",
  },
  {
    ID: "2",
    Name: "広東語",
  },
  {
    ID: "3",
    Name: "韓国・朝鮮語",
  },
  {
    ID: "4",
    Name: "フランス語",
  },
  {
    ID: "5",
    Name: "ドイツ語",
  },
  {
    ID: "6",
    Name: "スペイン語",
  },
  {
    ID: "7",
    Name: "タイ語",
  },
  {
    ID: "8",
    Name: "インドネシア語",
  },
  {
    ID: "9",
    Name: "イタリア語",
  },
  {
    ID: "10",
    Name: "ロシア語",
  },
  {
    ID: "11",
    Name: "ポルトガル語",
  },
  {
    ID: "12",
    Name: "マレーシア語",
  },
  {
    ID: "13",
    Name: "ベトナム語",
  },
  {
    ID: "14",
    Name: "アラビア語",
  },
  {
    ID: "15",
    Name: "タガログ語",
  },
  {
    ID: "16",
    Name: "台湾語",
  },
  {
    ID: "17",
    Name: "オランダ語",
  },
  {
    ID: "18",
    Name: "スウェーデン語",
  },
  {
    ID: "19",
    Name: "ヒンディー語",
  },
  {
    ID: "99",
    Name: "その他",
  },
] as const;

// 運転免許証オプション（基本情報用）
export const DRIVER_LICENCE_OPTIONS = [
  {
    ID: "1",
    Name: "なし",
  },
  {
    ID: "2",
    Name: "あり（AT車限定）",
  },
  {
    ID: "3",
    Name: "あり（MT車）",
  },
] as const;

// 性別オプション
export const GENDER_OPTIONS = [
  {
    ID: "2",
    Name: "女性",
  },
  {
    ID: "1",
    Name: "男性",
  },
] as const;

// 転職回数オプション
export const EXPERIENCE_COMPANY_OPTIONS = [
  {
    ID: "1",
    Name: "0社",
  },
  {
    ID: "2",
    Name: "1社",
  },
  {
    ID: "3",
    Name: "2社",
  },
  {
    ID: "4",
    Name: "3社",
  },
  {
    ID: "5",
    Name: "4社",
  },
  {
    ID: "6",
    Name: "5社",
  },
  {
    ID: "7",
    Name: "6社",
  },
  {
    ID: "8",
    Name: "7社",
  },
  {
    ID: "9",
    Name: "8社",
  },
  {
    ID: "10",
    Name: "9社",
  },
  {
    ID: "11",
    Name: "10社以上",
  },
] as const;

// マネジメント経験年数オプション
export const MANAGEMENT_EXPERIENCE_OPTIONS = [
  {
    ID: "1",
    Name: "経験なし",
  },
  {
    ID: "2",
    Name: "1年未満",
  },
  {
    ID: "3",
    Name: "1年以上",
  },
  {
    ID: "4",
    Name: "2年以上",
  },
  {
    ID: "5",
    Name: "3年以上",
  },
  {
    ID: "6",
    Name: "4年以上",
  },
  {
    ID: "7",
    Name: "5年以上",
  },
  {
    ID: "8",
    Name: "6年以上",
  },
  {
    ID: "9",
    Name: "7年以上",
  },
  {
    ID: "10",
    Name: "8年以上",
  },
  {
    ID: "11",
    Name: "9年以上",
  },
  {
    ID: "12",
    Name: "10年以上",
  },
] as const;

// マネジメント人数オプション
export const MANAGEMENT_PEOPLE_OPTIONS = [
  {
    ID: "1",
    Name: "1〜4人",
  },
  {
    ID: "2",
    Name: "5〜9人",
  },
  {
    ID: "3",
    Name: "10〜29人",
  },
  {
    ID: "4",
    Name: "30〜99人",
  },
  {
    ID: "5",
    Name: "100人以上",
  },
] as const;

// 従業員数オプション
export const EMPLOYEE_NUMBER_OPTIONS = [
  {
    ID: "1",
    Name: "10人未満",
  },
  {
    ID: "2",
    Name: "10〜29人",
  },
  {
    ID: "3",
    Name: "30〜99人",
  },
  {
    ID: "4",
    Name: "100〜299人",
  },
  {
    ID: "5",
    Name: "300〜999人",
  },
  {
    ID: "6",
    Name: "1000〜2999人",
  },
  {
    ID: "7",
    Name: "3000人以上",
  },
] as const;

// 雇用形態オプション（キャリア用）
export const EMPLOYMENT_TYPE_OPTIONS = [
  {
    ID: "1",
    Name: "正社員",
  },
  {
    ID: "2",
    Name: "契約社員",
  },
  {
    ID: "3",
    Name: "役員（任用契約）",
  },
  {
    ID: "4",
    Name: "業務委託",
  },
  {
    ID: "5",
    Name: "派遣社員",
  },
  {
    ID: "6",
    Name: "アルバイト",
  },
] as const;

// 転職希望時期オプション
export const JOB_CHANGE_PERIOD_OPTIONS = [
  {
    ID: "1",
    Name: "1ヶ月以内",
  },
  {
    ID: "2",
    Name: "3ヶ月以内",
  },
  {
    ID: "3",
    Name: "6ヶ月以内",
  },
  {
    ID: "4",
    Name: "1年以内",
  },
  {
    ID: "5",
    Name: "1年よりも先",
  },
  {
    ID: "6",
    Name: "転職を考えていない",
  },
] as const;

// 役職オプション
export const EMPLOYMENT_POST_OPTIONS = [
  {
    ID: "1",
    Name: "役職なし",
  },
  {
    ID: "2",
    Name: "係長／リーダークラス",
  },
  {
    ID: "3",
    Name: "課長／マネージャークラス",
  },
  {
    ID: "4",
    Name: "部長／ゼネラルマネージャークラス",
  },
  {
    ID: "5",
    Name: "役員クラス",
  },
  {
    ID: "6",
    Name: "代表クラス",
  },
] as const;

// マネジメント経験年数オプション（詳細版）
export const JOBTYPE_EXPERIENCE_OPTIONS = [
  {
    ID: "2",
    Name: "1年未満",
  },
  {
    ID: "3",
    Name: "1年以上",
  },
  {
    ID: "4",
    Name: "2年以上",
  },
  {
    ID: "5",
    Name: "3年以上",
  },
  {
    ID: "6",
    Name: "4年以上",
  },
  {
    ID: "7",
    Name: "5年以上",
  },
  {
    ID: "8",
    Name: "6年以上",
  },
  {
    ID: "9",
    Name: "7年以上",
  },
  {
    ID: "10",
    Name: "8年以上",
  },
  {
    ID: "11",
    Name: "9年以上",
  },
  {
    ID: "12",
    Name: "10年以上",
  },
] as const;

// 言語レベルオプション
export const LANG_LEVEL_OPTIONS = [
  {
    ID: "1",
    Name: "あてはまるものはない",
  },
  {
    ID: "2",
    Name: "日常会話レベル",
  },
  {
    ID: "3",
    Name: "ビジネス会話レベル",
  },
  {
    ID: "4",
    Name: "ネイティブレベル",
  },
] as const;

// 学校種別オプション
/*
  大学院　　　 → 満24歳で卒業
  大学　　　　 → 満22歳で卒業
  短期大学　　 → 満20歳で卒業
  専門学校　　 → 満20歳で卒業
  高等専門学校 → 満20歳で卒業
  高等学校　　 → 満18歳で卒業
  中学校　　　 → 満15歳で卒業
*/
export const SCHOOL_TYPE_OPTIONS = [
  {
    ID: "1",
    Name: "大学院",
    AgeAtGraduation: 24,
  },
  {
    ID: "2",
    Name: "大学",
    AgeAtGraduation: 22,
  },
  {
    ID: "3",
    Name: "短期大学",
    AgeAtGraduation: 20,
  },
  {
    ID: "4",
    Name: "専門学校",
    AgeAtGraduation: 20,
  },
  {
    ID: "5",
    Name: "高等専門学校",
    AgeAtGraduation: 20,
  },
  {
    ID: "6",
    Name: "高等学校",
    AgeAtGraduation: 18,
  },
  {
    ID: "7",
    Name: "中学校",
    AgeAtGraduation: 15,
  },
] as const;
