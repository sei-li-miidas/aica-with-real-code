// 確約年収の下限提示タイプ
export const INCOME_FROM_TYPE = {
  EACH: 1, // 個別に提示
  UNIFORM: 2, // 一律提示（初期値）
  CURRENT: 3, // 現年収を提示
  DESIRED: 4, // 希望年収を提示
} as const;
