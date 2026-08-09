// 求人一覧の種別
// リストIDとは別。
export const LIST_TYPE = {
  ALL: "all", // すべての求人
  THEME: "theme", // テーマ別一覧
  TRASHED: "trashed", // 削除済み
  APPLY_PROMOTION: "apply_promotion", // 応募促進用の求人

  OUTSOURCING: "outsourcing",
} as const;

// リストIDの内アクション済みテーマ
export const ACTIONED_THEME_ID = {
  READ: "read", // 閲覧済み
  STARRED: "starred", // 気になる
  TRASHED: "trashed", // 削除済み
} as const;

// 求人リストの並び替え
export const ORDER_TYPE = {
  RECOMMEND: "miidas_recommend", // ミイダスおすすめ順
  RECENT: "newest", // 新着順
  INCOME: "income_from", // 年収順
  TRASHED_AT: "trashed_at", // ゴミ箱日時順
} as const;

// 求人リストの並び替えの名前
export const ORDER_TYPE_NAME = {
  RECOMMEND: "ミイダスおすすめ順", // ミイダスおすすめ順
  RECENT: "新着順", // 新着順
  INCOME: "年収順", // 年収順
} as const;

// 求人リストの並び替えタイプと名前のマップ
export const ORDER_TYPE_NAME_MAP = {
  [ORDER_TYPE.RECOMMEND]: ORDER_TYPE_NAME.RECOMMEND,
  [ORDER_TYPE.RECENT]: ORDER_TYPE_NAME.RECENT,
  [ORDER_TYPE.INCOME]: ORDER_TYPE_NAME.INCOME,
} as const;

// 並び替えのデフォルト値
export const DEFAULT_ORDER_TYPE = ORDER_TYPE.RECOMMEND;
export const DEFAULT_ORDER2_TYPE = ORDER_TYPE.RECENT;
// 社員求人一覧の並び替えのデフォルト値
export const DEFAULT_ORDER_TYPE_EMPLOYEE = ORDER_TYPE.RECOMMEND;
export const DEFAULT_ORDER2_TYPE_EMPLOYEE = ORDER_TYPE.RECENT;
export const DEFAULT_ORDER2_TYPE_EMPLOYEE_APPLIED = ORDER_TYPE.RECENT;

// 非表示の求人のデフォルトソート
export const DEFAULT_ORDER_TYPE_TRASHED = ORDER_TYPE.TRASHED_AT;
export const DEFAULT_ORDER2_TYPE_TRASHED = ORDER_TYPE.RECENT;

// カテゴリーバーのセクション名
export const CATEGORY_SECTION_NAME = {
  RECOMMEND_UNSATISFIED: "recommendUnsatisfied", // 不一致
} as const;

// カテゴリーバーのセクションのタイトル名
export const CATEGORY_SECTION_TITLE = {
  [CATEGORY_SECTION_NAME.RECOMMEND_UNSATISFIED]: "あなたにおすすめの求人",
} as const;

// 求人リストアイテムのアクションステータス
export const APPLICATION_STATUS = {
  APPLY: "応募済み",
  APPLY_CONDITIONAL: "条件交渉済み",
  MEETING: "面談希望済み",
  QUESTION: "質問済み",
} as const;

// ユーザーへのアプローチ種別（トークに紐づいたステータス）
// NOTE: 旧APPLICATION_TYPE。 既読・気になるが応募と独立しているため、派生の新規パラメータとして差し替え。（#64384）
export const APPROACH_TYPE = {
  READ: 0, // 求人詳細既読
  // 1 // フォロー *廃止されているが、メッセージがあるフォロートークは残っている
  STARRED: 2, // 気になる
  APPLY: 3, // 面確応募
  APPLY_CONDITIONAL: 4, // 条件付き応募 NOTE: #60237 により以降生まれない想定
  APPLY_EXPIRED: 5, // 期限切れ応募&非面確応募
  APPLY_CAPACITY_OVER: 6, // 定員オーバー応募
  MEETING: 7, // 面談希望
  QUESTION: 8, // 求人への質問
  PARTNER_APPLY: 9, // HP応募
  // 10 // 他媒体応募(コンピテンシー)
  // 11 // 他媒体応募(バイアスゲーム)
} as const;

// 求人が0件の場合のリンクパス
export const OFFER_EMPTY_PATH = {
  PROFILE: "/profile", // プロフィール
  PROFILE_DOCS: "/profile/docs/upload", // 応募書類の登録
  WISH: "/wish", // 希望条件設定
} as const;

// フィルターモーダル表示用の情報
export const FILTER_INFO = {
  CERTIFICATED: {
    TITLE: "ミイダス認定",
    ID: "Certificated",
    NAME: "certificated",
    ALL_LABEL: "すべて",
    INCLUDE_LABEL: "ミイダス認定取得のみ",
    HELP: {
      title: null,
      text: "ミイダス認定とは、ミイダスが推奨している企業情報などを登録し、ユーザーの効率的な転職活動に貢献している企業を認定するものです。認定企業からのスカウトはより詳しい企業情報などが登録されているため、面接前から自分の求めている企業像に合っているかどうかをしっかりと検討できます。",
    },
  },
  BROWSED: {
    TITLE: "閲覧",
    ID: "Browsed",
    NAME: "browsed",
    ALL_LABEL: "すべて",
    INCLUDE_LABEL: "閲覧済み",
    EXCLUDE_LABEL: "閲覧していない",
  },
  SCOUT_MESSAGE: {
    TITLE: "スカウトメッセージ",
    ID: "ScoutMessage",
    NAME: "scout_message",
    ALL_LABEL: "すべて",
    INCLUDE_LABEL: "メッセージありのみ",
  },
} as const;

// 社員求人で有効なフィルター一覧
export const EMPLOYEE_FILTER_INFO_LIST = [
  FILTER_INFO.CERTIFICATED,
  FILTER_INFO.BROWSED,
  FILTER_INFO.SCOUT_MESSAGE,
] as const;

// フィルターの値
export const FILTER_VALUE = {
  ALL: "all",
  INCLUDE: "include",
  EXCLUDE: "exclude",
} as const;

// リモートワークのAPIインターフェイス
export const REMOTE_WORK_TYPE = {
  NULL: null, // 企業で未入力の場合（指定なし）
  NG: 1, // リモート不可
  CONDITIONAL: 2, // リモートOK（条件なし）
  OK: 3, // リモートOK（条件なし）
} as const;

// リモートワークのラベル
export const REMOTE_WORK_LABEL = {
  OK: "リモート勤務OK",
  NG: "リモート勤務NG",
  CONDITIONAL: "リモート勤務OK（条件つき）",
} as const;

export const BROWSED_CARD_LOG_SEND_INTERVAL = 5000;

/**
 * マッチ度ランク
 */
export const MATCH_RATE_RANK = {
  A_PLUS: {
    ID: 1,
    NAME: "A", // +は画像で表示するため
  },
  A: {
    ID: 2,
    NAME: "A",
  },
  B: {
    ID: 3,
    NAME: "B",
  },
} as const;
