import { Record } from "immutable";

type Props = {
  /** その面接方法が企業側で設定されているか否か */
  EnableFlg: boolean;
  /** 可能平日時間From */
  PossibleWeekdayHourFrom: number | null;
  /** 可能平日時間To */
  PossibleWeekdayHourTo: number | null;
  /** 土日祝日可能フラグ */
  PossibleWeekendFlg: boolean;
  /** 可能日時補足 */
  PossibleTimeComplement: string | null;
  /** 所要時間（分） */
  Minutes: number;
};

/**
 * InterviewOnline
 * 面接方法：オンライン の設定情報のレコード
 */
export default class InterviewOnline extends Record<Props>({
  EnableFlg: false,
  PossibleWeekdayHourFrom: null,
  PossibleWeekdayHourTo: null,
  PossibleWeekendFlg: false,
  PossibleTimeComplement: null,
  Minutes: 0,
}) {}
