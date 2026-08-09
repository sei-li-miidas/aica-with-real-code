import { Record, OrderedSet } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";

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
  /** イベント場所候補 */
  PlaceOptions: OrderedSet<string>;
  /** 交通費支給フラグ */
  TransportationPaymentFlg: boolean;
  /** 交通費支給（備考） */
  TransportationPaymentRemarks: boolean;
};

/**
 * InterviewMeeting
 * 面接方法：会う の設定情報のレコード
 */
export default class InterviewMeeting extends Record<Props>({
  EnableFlg: false,
  PossibleWeekdayHourFrom: null,
  PossibleWeekdayHourTo: null,
  PossibleWeekendFlg: false,
  PossibleTimeComplement: null,
  Minutes: 0,
  PlaceOptions: OrderedSet([]),
  TransportationPaymentFlg: false,
  TransportationPaymentRemarks: false,
}) {
  constructor(interview: RecordConstructorParameter<InterviewMeeting>) {
    const placeOptionSet = interview.PlaceOptions
      ? // @ts-expect-error: 型エラーが起きないよう後で修正する
        OrderedSet(interview.PlaceOptions)
      : OrderedSet([]);
    const interviewRecord = { ...interview, PlaceOptions: placeOptionSet };

    // @ts-expect-error: 型エラーが起きないよう後で修正する
    super(interviewRecord);
  }
}
