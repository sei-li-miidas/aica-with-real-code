// 求人の面接方法
export const EVENT_METHOD = {
  NONE: 0, // 未指定（初期値）
  MEETING: 1, // 直接会う
  PHONE: 2, // 電話
  ONLINE: 3, // オンライン面接
} as const;

// 求人の面接日時の調整
export const EVENT_ADJUSTMENT = {
  NONE: 0, // 未指定（初期値）
  SPECIFIED: 1, // 指定する
  UNSPECIFIED: 2, // 指定しない
} as const;

// 面接回数
export const INTERVIEW_TIMES = {
  NONE: {
    ID: 0,
    Name: "面接回数を記載しない",
  },
  ONE: {
    ID: 1,
    Name: "１回",
  },
  TWO: {
    ID: 2,
    Name: "２回",
  },
  THREE: {
    ID: 3,
    Name: "３回",
  },
  FOUR: {
    ID: 4,
    Name: "４回以上",
  },
} as const;

export const OFFER_TALK_STATE = {
  LIGHT_MESSAGE: "LightMessage", // ライトメッセージ
  TALK: "Talk", // 通常トーク
} as const;

// スカウトメッセージのタイプ
export const SCOUT_MESSAGE_TYPE = {
  SCOUT: 1, // スカウトメッセージ
  FIRST_REMIND: 2, // リマインドメッセージ1回目
  SECOND_REMIND: 3, // リマインドメッセージ2回目
} as const;

// 求人訴求のタイプ
export const POSITION_APPEAL_TYPE = {
  NONE: 0, // 未指定（初期値）
  STARRED: 1, // 気になる求人
  SIMILAR: 2, // 類似求人
  RECOMMENDED: 3, // オススメ求人
} as const;

// マッチング成立モーダルの表示状態
export const MATCHING_MODAL_DISPLAY_MODE = {
  NONE: "none", // 表示なし
  LIST: "list", // 一覧で表示した場合
  DETAIL: "detail", // 詳細で表示した場合
} as const;
