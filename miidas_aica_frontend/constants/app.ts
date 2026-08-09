// メッセージ送信者タイプ
export const ACTOR_TYPE = {
  USER: 1, // メッセージ送信者がユーザー
  COMPANY: 2, // メッセージ送信者が企業
  SYSTEM: 3, // メッセージ送信者がミイダス
} as const;

// ネイティブに送信する際の識別子
export const SEND_NATIVE_BRIDGE_TYPE = {
  APP_SWIPE_ENABLED: "ON", // アプリのスワイプ制御を有効にする際の識別子
  APP_SWIPE_DISABLED: "OFF", // アプリのスワイプ制御を無効にする際の識別子
} as const;

// // ネイティブから受信する際の識別子
// export const RECIVE_NATIVE_BRIDGE_TYPE = {
//   OFFER_ITEM_CHECK_MODE_ON: 'ON', // ポジションアイテムのチェックモードを有効にする識別子
//   OFFER_ITEM_CHECK_MODE_OFF: 'OFF', // ポジションアイテムのチェックモードを無効にする識別子
// };

// 個人のお客様向けのヘルプページのURL（本番環境のみ存在するページの為、localやdev等の出し分け不要）
export const URL_HELP = `https://support.miidas.jp/?kinds=${encodeURIComponent("個人のお客様")}`;
// アプリからヘルプページに遷移させる際のURL
export const URL_HELP_APP = `https://support.miidas.jp/?kinds=${encodeURIComponent("個人のお客様")}&inapp=true`;

// ネイティブに渡すヘッダーカラーの識別子
export const CHANGE_HEADER_COLOR_TYPE = {
  NORMAL: "Normal",
  TRASH: "TrashCan",
  PENDING: "Pending", // あえて何もしないキー。後続に非同期色変更があるときなどに使う
} as const;

// トースト通知の表示期間（ms）
export const NOTIFICATION_WAIT_TIME = 1800;

// 再認証リダイレクトまでの期間（ms）
export const AUTH_REDIRECT = {
  PATH: "/login",
  WAIT_TIME: 3000,
} as const;

// トークステータス(miidas_go/domain/connect/enum/talk.go参照)
export const TALK_STATUS = {
  COMPANY_BALL_CANCEL: 1, // 企業メッセージ送信待ちキャンセル
  COMPANY_BALL: 2, // 企業メッセージ送信待ち
  COMPANY_MESSAGED: 3, // 企業メッセージ送信済み、ユーザー返信待ち
  CONNECTED_APPLIED_WITH_CONDITIONS: 4, // トーク中（条件付応募済み、企業返信待ち）
  CONNECTED_FREE_TALKING: 5, // トーク中（フリートーク中）
  CONNECTED_APPLY_OR_MEETING_OR_INQUIRY: 6, // トーク中（応募・面談希望・質問済み、企業返信待ち）
  INTERRUPTED: 7, // トーク中断
  ENDED: 8, // トーク終了（ユーザー退会済み）
} as const;

// テキストの省略基準文字数
export const TEXT_OMITTED_LENGTH = 220;
// テキストの省略基準行数
export const TEXT_OMITTED_NUMBER_OF_LINES = 8;
// ReadMoreTextコンポーネントの「続きを見る」をJSコードで展開するために参照するCSSクラス名
export const READ_MORE_BUTTON_CLS = "js-readMoreText_ReadMoreBtn-show";
export const READ_MORE_INDUSTRY_RESEARCH_BUTTON_CLS =
  "js-readMoreText_ReadMoreIndustryResearchBtn"; // 「業界研究」だけ開く用
// Collapseコンポーネントの「詳細を見る」をJSコードで展開するために参照するCSSクラス名
export const EXPAND_BUTTON_CLS = "js-collapseToggleBtn-show";

// APIのリクエストヘッダのキー
export const REQUEST_HEADERS = {
  IF_POSITION_UNMODIFIED_SINCE: "X-Miidas-If-Position-Unmodified-Since", // ポジション情報の最終更新日時、古い情報で応募を行わないようにするため
  FRONTEND_API_VERSION: "X-Miidas-Frontend-Api-Version", // フロントエンドAPIバージョン
  MIIDAS_CONTEXT: "X-Miidas-Context", // ログなどに使用するコンテキストデータ
  LP_CHANNEL_CONTEXT: "X-Miidas-Context", // LPチャネルデータ
  IS_PWA: "X-Miidas-Is-Pwa", // PWAかどうかの判定
} as const;

// サーバのエラーコード @see https://github.com/MIIDAS-Company/miidas_go/blob/develop/message/messages.go
export const SERVER_ERROR_CODES = {
  A0011: "A0011", // ファイルが見つからない場合
  A0007: "A0007", // IDが不正
  A0010: "A0010", // 入力が不正
  A0018: "A0018", // トークンが期限切れ
  A0046: "A0046", // コンピテンシー診断 非公開設定(ユーザーの過去現在の在籍企業など)している企業に対し他社応募
  A0060: "A0060", // メール送信失敗
  A0066: "A0066", // 社員ユーザーのセッションがない、またはログイン状態でない場合
  A0067: "A0067", // ログインしようとしているシークレットユーザーは通常アカウントへ移行済み
  A0068: "A0068", // メールアドレスまたはパスワードの不一致
  A0081: "A0081", // 応募しようとしたスカウトの情報が閲覧後に更新されている
  A0100: "A0100", // 入力値エラー(NotFound), 企業ステータスが不正
  A0101: "A0101", // 存在しないリソース指定(NotFound)
  A0102: "A0102", // リソースのコンフリクト(StatusConflict)
  A0134: "A0134", // 応募済み
  E0001: "E0001", // データ不整合
  E0005: "E0005", // 権限がないので参照できない。
  I0002: "I0002", // // 権限がないので参照できない。（ログレベル違い）
  // ミイダス2.0のエラーコード @see https://github.com/MIIDAS-Company/miidas_go/blob/develop/sdk/error/common_app_errors.go
  INVALID_REQUEST: 1, // 無効なリクエスト
  FORBIDDEN_STATUS: 3, // 閲覧禁止
  RESOURCE_NOT_FOUND: 4, // リソースが見つからない場合
  INVALID_STATUS: 5, // 無効な状態
  // 2.0のサーバーエラーコードの持ち方をフロントの議題に挙げています。
  // https://github.com/MIIDAS-Company/miidas_user_next/pull/971#discussion_r808597506
  // バックの汎用バリデーションのエラーコード
  VALIDATION: {
    UNKNOWN: 0,
    REQUIRED: 1,
    LESS: 2,
    MORE: 3,
    INVALID: 9,
    NOT_MATCH: 10,
    EMAIL_DUPLICATE: 12, // こいつだけresponse.status が 409 なので注意
    EMAIL_ACCOUNT: 16,
  },
  // バックのサービスごとにエラー番号を管理する
  // NOTE: APIは[サービス名]/api/v1/hoge のような形になっている. 今後v1の部分は消えるらしい
  SERVICE: {
    APPLY: {
      ERROR_1002: 1002, // 応募しようとしたポジションの情報が閲覧後に更新されている
      ERROR_1003: 1003, // 応募しようとしたポジションがすでに応募済み
      ERROR_1015: 1015, // スポットの熟練度に回答済み
      ERROR_1016: 1016, // 非表示の求人に応募
    },
    USER_ACCOUNT: {
      ERROR_1006: 1006, // メールアドレス認証済みエラー
      ERROR_1009: 1009, // 電話番号重複エラー
    },
    USER_ENTRY: {
      /** メールアドレス形式エラー */
      ERROR_1012: 1012,
      /** 受験済みエラー */
      ERROR_1013: 1013,
      /** 受験期間外エラー */
      ERROR_1014: 1014,
    },
  },
} as const;

// // 機能トグル用の機能一覧
// export const FEATURES = {
// };

// /**
//  * NOP
//  * 空関数
//  * Reactコンポーネントprops設定にその場で空関数を記載する場合、毎回新しい空関数と認識されるため、無駄なレンダリングが発生することがある。
//  * それを避けるためには代わりにここの空関数の定数を使うと想定する。
//  */
export const NOP = () => {};

/**
 * NULL
 * nullを返す関数
 */
export const NULL = () => null;

// ナビボタン（ヘッダーの左側ボタン）の種類
export const HEADER_NAVI_BUTTON_TYPE = {
  HOME: "HOME", // ホームへ戻るボタン
  BACK: "BACK", // 戻るボタン
  NONE: "NONE", // 非表示
  CUSTOM: "CUSTOM", // カスタムボタン
} as const;

// 400エラーページ
export const ERROR_PAGE_404 = {
  TITLE: "404 Not Found\nお探しのページは見つかりません。",
  MESSAGE:
    "お探しのページはURLが変更されたか、削除された可能性があります。\nまた、正しくURLが入力されているかご確認ください。",
} as const;

// 500エラーページ
export const ERROR_PAGE_500 = {
  TITLE: "500 Internal Server Error\nお探しのページを表示できません。",
  MESSAGE:
    "お探しのページは一時的にアクセスできない状態にあるか、システムエラーが発生しております。\nお手数ですがしばらく時間を置いてから再度お試しください。",
} as const;

// 登録企業数
export const REGISTERED_CORPORATIONS = 313000;

// デバイス別Canvasサイズ
export const DEVICE_CANVAS_SIZE = {
  // PC
  PC: {
    canvasWidth: 960, // canvasの物理サイズ幅（* window.devicePixelRatio）
    canvasHeight: 1350, // canvasの物理サイズ高さ（* window.devicePixelRatio）
    canvasStyle: {
      width: 960, // canvasの論理サイズ幅
      height: 1350, // canvasの論理サイズ高さ
    },
    scale: 1.7, // 伸縮率（* window.devicePixelRatio）
  },
  // スマホ
  SP: {
    canvasWidth: 310,
    canvasHeight: 800,
    canvasStyle: {
      width: 310,
      height: 800,
    },
    scale: 1, // 伸縮率（= window.devicePixelRatio）
  },
} as const;

// 氏名と電話番号の登録モーダルの種類
export const MODAL_NAME_AND_PHONE_REGISTER_TYPE = {
  TALKS: "talks",
  ONE_CLICK_APPLICATION: "oneClickApplication",
  MEETING: "meeting",
} as const;

// 氏名と電話番号の登録モーダルがどの文脈で表示されたか計測するためのコンテキストタイプ
export const MODAL_NAME_AND_PHONE_REGISTER_CONTEXT_TYPE = {
  APPLICATION: "application",
  EXAM_APPLY: "examApply",
  PARTNER_APPLY: "partnerApply",
} as const;

/**
 * タブバーからの遷移先一覧
 */
export const TAB_BAR_LINK_PATH = {
  DASHBOARD: "/dashboard",
  EMPLOYEE_OFFER_LIST: "/offer/employee",
  EMPLOYEE_STARRED_OFFER_LIST: "/offer/employee/starred",
  TALKS: "/talks",
  MY_PAGE: "/settings",
} as const;

/**
 * タブバーを表示するパス一覧
 */
export const TAB_BAR_DISPLAY_PATH = {
  DASHBOARD: TAB_BAR_LINK_PATH.DASHBOARD,
  EMPLOYEE_OFFER_LIST: TAB_BAR_LINK_PATH.EMPLOYEE_OFFER_LIST,
  EMPLOYEE_STARRED_OFFER_LIST: TAB_BAR_LINK_PATH.EMPLOYEE_STARRED_OFFER_LIST,
  OUTSOURCING_STARRED_OFFER_LIST: "/offer/outsourcing/starred",
  TALKS: TAB_BAR_LINK_PATH.TALKS,
  MY_PAGE: TAB_BAR_LINK_PATH.MY_PAGE,
} as const;

/**
 * アプリで、タブバーを表示するパス以外で「表示するパスとアクティブになるタブバーアイテム」が決まっているもの
 */
const APP_TAB_BAR_ACTIVE_PATH_MAP = {
  WISH: "/wish",
  WISH_SETTING: "/wish/setting",
} as const;

/**
 * アプリのタブバーのインデックス
 */
export const APP_TAB_BAR_INDEX = {
  DASHBOARD: 0,
  EMPLOYEE_OFFER_LIST: 1,
  EMPLOYEE_STARRED_OFFER_LIST: 2,
  TALKS: 3,
  MY_PAGE: 4,
} as const;

/**
 * アプリで、表示するパスとアクティブになるタブバーアイテムの対応関係マップ
 */
export const APP_TAB_BAR_INDEX_BY_PATHNAME = {
  [TAB_BAR_LINK_PATH.DASHBOARD]: APP_TAB_BAR_INDEX.DASHBOARD,
  [TAB_BAR_LINK_PATH.EMPLOYEE_OFFER_LIST]:
    APP_TAB_BAR_INDEX.EMPLOYEE_OFFER_LIST,
  // NOTE: タブバー表示画面の/offer/employeeと同じタブで表示しないと、検索条件変更を引き継げないため
  [APP_TAB_BAR_ACTIVE_PATH_MAP.WISH]: APP_TAB_BAR_INDEX.EMPLOYEE_OFFER_LIST,
  [APP_TAB_BAR_ACTIVE_PATH_MAP.WISH_SETTING]:
    APP_TAB_BAR_INDEX.EMPLOYEE_OFFER_LIST,

  [TAB_BAR_LINK_PATH.EMPLOYEE_STARRED_OFFER_LIST]:
    APP_TAB_BAR_INDEX.EMPLOYEE_STARRED_OFFER_LIST,
  [TAB_BAR_DISPLAY_PATH.OUTSOURCING_STARRED_OFFER_LIST]:
    APP_TAB_BAR_INDEX.EMPLOYEE_STARRED_OFFER_LIST,
  [TAB_BAR_LINK_PATH.TALKS]: APP_TAB_BAR_INDEX.TALKS,
  [TAB_BAR_LINK_PATH.MY_PAGE]: APP_TAB_BAR_INDEX.MY_PAGE,
} as const;

/**
 * ユーザーにアクションを求める注意喚起の種類
 */
export const ACTION_REQUIRED_STATUS = {
  IN_PROGRESS: "inProgress",
} as const;

// messageイベントハンドラーで処理を分岐するための値
export const POST_MESSAGE_TYPE = {
  SHOW_SEND_EXAM_POPUP_AFTER_COMPETENCY_COMPLETE:
    "SHOW_SEND_EXAM_POPUP_AFTER_COMPETENCY_COMPLETE",
  GET_FIRST_POPUP: "GET_FIRST_POPUP",
} as const;

// タブバーに表示する通知カウントの上限
export const MAX_TAB_BAR_NOTIFICATION_COUNT = 99;

// テーマ
export const THEMES = {
  DEFAULT: {
    "--color-primary": "var(--color-light-blue-800)",
    "--color-primary-dark": "var(--color-light-blue-1000)",
  },
} as const;

/**
 * 登録フローのページタイプ
 */
export const ENTRY_PART1_PAGE_TYPE = {
  /** 扉絵 */
  COVER: "cover",
  /** 質問 */
  QUESTION: "question",
  /** アカウント登録 */
  ACCOUNT: "account",
  /** その他 */
  OTHER: "other",
} as const;

/**
 * 登録フローPart2のページタイプ
 */
export const ENTRY_PART2_PAGE_TYPE = {
  /** 質問 */
  QUESTION: "question",
} as const;

/**
 * 登録フローPart1のステップタイプ
 */
export const ENTRY_PART1_PAGE_STEP_TYPE = {
  /** プロフィール */
  PROFILE: 1,
  /** 職務経歴 */
  CAREER: 2,
  /** 実務経験 */
  SKILL: 3,
  /** 語学・資格 */
  LICENCE: 4,
  /** アカウント登録 */
  ACCOUNT: "accont",
} as const;

/**
 * 音声入力モードの無音の閾値
 */
export const VOICE_INPUT_SILENCE_THRESHOLD: number = 3000;

/**
 * 音声自動送信タイマーバーの色
 */
export const COLOR_TIMEOUT_100 = "#234ae8"; // 100%の長さ
export const COLOR_TIMEOUT_75 = "#5755e3"; // 75%の長さ
export const COLOR_TIMEOUT_50 = "#8a5fde"; // 50%の長さ
export const COLOR_TIMEOUT_25 = "#be6ad9"; // 25%の長さ
export const COLOR_TIMEOUT_0 = "#f174d4"; // 0%の長さ
