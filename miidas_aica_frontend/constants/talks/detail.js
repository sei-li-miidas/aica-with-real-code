// 求人詳細のタブ
export const POSITION_DETAIL_TABS = {
  // NOTE: PositionDetailsのみAPIの戻り値と合わせている。アプリとの連携に使っているので独断で変えないように注意。
  POSITION_DETAILS: "PositionDetails", // 求人詳細画面

  JOB_DESCRIPTION: "JobDescription", // 募集要項タブ
  INTERVIEW_SETTINGS: "InterviewSettings", // 選考方法タブ
  COMPANY_OVERVIEW: "CompanyOverview", // 企業情報タブ
  INDUSTRY_RESEARCH: "IndustryResearch", // 業界研究タブ(日経バリューサーチリスト)
};

// メッセージの最大文字数
export const MESSAGE_MAX_LENGTH = 2000;

// トークメッセージの日時範囲パターン
// YYYY/MM/DD（ddd）HH:mm〜HH:mm の形式
export const TALK_DATETIME_RANGE_PATTERN =
  "[0-9]{4}/(0[1-9]|1[0-2])/(0[1-9]|[1-2][0-9]|3[0-1])（(日|月|火|水|木|金|土)）(2[0-3]|[01][0-9]):[0-5][0-9]〜(2[0-3]|[01][0-9]):[0-5][0-9]";

// 支払い代行メッセージのイベントタイプ
export const PAYMENT_PROXY_MESSAGE_EVENT_TYPE = {
  REGISTERED: 1, // 本申請
  AGREED: 2, // 同意
  DISAGREED: 3, // 非同意
  CANCELED: 4, // 企業側キャンセル
};

// 支払い代行メッセージのメッセージタイプ
export const PAYMENT_PROXY_MESSAGE_TYPE = "PaymentProxy";
