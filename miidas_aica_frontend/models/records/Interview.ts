import { Record, List } from "immutable";
import * as CONST_OFFER from "@/constants/offers/detail";
import MasterV2Record from "@/models/records/MasterV2";
import InterviewMeetingRecord from "@/models/records/InterviewMeeting";
import InterviewPhoneRecord from "@/models/records/InterviewPhone";
import InterviewOnlineRecord from "@/models/records/InterviewOnline";
import WorkExperienceRecord from "@/models/records/WorkExperience";
import {
  type RecordConstructorParameter,
  type ValuesType,
  getKeys,
} from "@/types/utility-types";

type Props = {
  /** 選考期間 */
  EstimatedTerm: string | null;
  /** 面接回数 */
  InterviewTimes: number | null;
  /** その他試験 適性試験 */
  SelectionAptitudeTestExists: boolean;
  /** その他試験 筆記試験 */
  SelectionPaperTestExists: boolean;
  /** その他試験 実技試験 */
  SelectionPracticalTestExists: boolean;
  /** その他試験 その他 */
  SelectionOtherTestExists: boolean;
  /** その他試験 補足 */
  SelectionRemarks: string;
  /** 面接時私服OK */
  CasualDressFlg: boolean;
  /** リアル職場体験 */
  WorkExperience: WorkExperienceRecord;
  /** 連絡先 */
  Contact: string;
  /** 面接官 */
  Interviewers: List<MasterV2Record>;
  /** 面接官（その他） */
  OtherInterviewer: string | null;
  /** 面接方法:会う */
  Meeting: InterviewMeetingRecord;
  /** 面接方法:電話 */
  Phone: InterviewPhoneRecord;
  /** 面接方法:オンライン */
  Online: InterviewOnlineRecord;
};

type EventMethodType = ValuesType<typeof CONST_OFFER.EVENT_METHOD>;

/**
 * Interview
 * 面接情報のレコード
 */
export default class Interview extends Record<Props>({
  EstimatedTerm: null,
  InterviewTimes: null,
  SelectionAptitudeTestExists: false,
  SelectionPaperTestExists: false,
  SelectionPracticalTestExists: false,
  SelectionOtherTestExists: false,
  SelectionRemarks: "",
  CasualDressFlg: false,
  WorkExperience: new WorkExperienceRecord({}),
  Contact: "",
  Interviewers: List([]),
  OtherInterviewer: null,
  Meeting: new InterviewMeetingRecord({}),
  Phone: new InterviewPhoneRecord({}),
  Online: new InterviewOnlineRecord({}),
}) {
  constructor(
    interview: RecordConstructorParameter<Interview> & {
      Shared?: RecordConstructorParameter<Interview>;
    },
  ) {
    // 共通設定（平坦にする）
    const shared = interview.Shared
      ? {
          EstimatedTerm: interview.Shared.EstimatedTerm || null,
          InterviewTimes: interview.Shared.InterviewTimes || null,
          SelectionAptitudeTestExists:
            interview.Shared.SelectionAptitudeTestExists || false,
          SelectionPaperTestExists:
            interview.Shared.SelectionPaperTestExists || false,
          SelectionPracticalTestExists:
            interview.Shared.SelectionPracticalTestExists || false,
          SelectionOtherTestExists:
            interview.Shared.SelectionOtherTestExists || false,
          SelectionRemarks: interview.Shared.SelectionRemarks || "",
          CasualDressFlg: interview.Shared.CasualDressFlg || false,
          OtherInterviewer: interview.Shared.OtherInterviewer || null,
          Contact: interview.Shared.Contact ?? "",
        }
      : null;
    // 面接官Recordのリストを生成
    const interviewerArray = interview.Shared?.Interviewers || [];
    // @ts-expect-error: 型エラーが起きないよう後で修正する
    const interviewers = interviewerArray.map((interviewer) => {
      return new MasterV2Record(interviewer);
    });

    // 面接方法：会う のrecordを作成
    const meetingImtRecord = interview.Meeting
      ? new InterviewMeetingRecord(interview.Meeting)
      : new InterviewMeetingRecord({});
    // 面接方法：電話 のrecordを作成
    const phoneImtRecord = interview.Phone
      ? new InterviewPhoneRecord(interview.Phone)
      : new InterviewPhoneRecord({});
    // 面接方法：オンライン のrecordを作成
    const onlineImtRecord = interview.Online
      ? new InterviewOnlineRecord(interview.Online)
      : new InterviewOnlineRecord({});

    // ポジション内容Recordを生成
    const interviewRecord = {
      ...shared,
      WorkExperience: new WorkExperienceRecord(interview.WorkExperience ?? {}),
      Interviewers: List(interviewers),
      Meeting: meetingImtRecord,
      Phone: phoneImtRecord,
      Online: onlineImtRecord,
    };

    // @ts-expect-error: 型エラーが起きないよう後で修正する
    super(interviewRecord);
  }

  /**
   * getEventRecord
   * 面接方法のレコードを返す
   */
  getEventRecord(eventMethod: EventMethodType) {
    switch (eventMethod) {
      case CONST_OFFER.EVENT_METHOD.MEETING:
        return this.Meeting;
      case CONST_OFFER.EVENT_METHOD.PHONE:
        return this.Phone;
      case CONST_OFFER.EVENT_METHOD.ONLINE:
        return this.Online;
      default:
        return null;
    }
  }

  /**
   * getEventPossibleDateTimeForDisplay
   * 表示用の面接可能日時を返す
   */
  getEventPossibleDateTimeForDisplay(eventMethod: EventMethodType) {
    const eventImtRecord = this.getEventRecord(eventMethod);
    if (!eventImtRecord) {
      return "";
    }

    let possibleTime = eventImtRecord.PossibleWeekdayHourFrom
      ? `${eventImtRecord.PossibleWeekdayHourFrom}時から`
      : "";
    if (eventImtRecord.PossibleWeekdayHourTo) {
      possibleTime = `${possibleTime}${eventImtRecord.PossibleWeekdayHourTo}時まで`;
    }
    if (possibleTime) {
      possibleTime = `平日${possibleTime}面接可能`;
    }

    if (eventImtRecord.PossibleWeekendFlg) {
      possibleTime = `${possibleTime} / 土日祝日の面接可能`;
    }

    return possibleTime;
  }

  /**
   * getEventTime
   * 面接所要時間を返す
   */
  getEventTime(eventMethod: EventMethodType) {
    const eventImtRecord = this.getEventRecord(eventMethod);
    if (!eventImtRecord) {
      return null;
    }
    return eventImtRecord.Minutes;
  }

  /**
   * getEventTimeForDisplay
   * 表示用の面接所要時間を返す
   */
  getEventTimeForDisplay(eventMethod: EventMethodType) {
    const eventImtRecord = this.getEventRecord(eventMethod);
    if (!eventImtRecord) {
      return "";
    }
    return `${eventImtRecord.Minutes / 60}時間`;
  }

  /**
   * getTransportationPaymentForDisplay
   * 表示用の面接交通費を返す
   */
  getTransportationPaymentForDisplay() {
    return this.Meeting.TransportationPaymentFlg ? "支給あり" : "支給なし";
  }

  /**
   * GetInterviewerForDisplay
   * 表示用の面接官を返す
   */
  getInterviewerForDisplay() {
    const interviewers = [];

    // 面接官
    if (this.Interviewers) {
      this.Interviewers.forEach((interviewer) => {
        interviewers.push(interviewer.Name);
      });
    }

    // 他の面接官
    if (this.OtherInterviewer) {
      interviewers.push(this.OtherInterviewer);
    }

    return interviewers.join(" / ");
  }

  /**
   * GetInterviewTimesForDisplay
   * 表示用の面接回数を返す
   */
  getInterviewTimesForDisplay() {
    const interviewTimes = this.InterviewTimes;
    if (
      !interviewTimes ||
      interviewTimes === CONST_OFFER.INTERVIEW_TIMES.NONE.ID
    ) {
      // 指定なしの場合は空
      return "";
    }
    const interviewTimesKey = getKeys(CONST_OFFER.INTERVIEW_TIMES).find(
      (key) => {
        return interviewTimes === CONST_OFFER.INTERVIEW_TIMES[key].ID;
      },
    );

    if (interviewTimesKey) {
      return CONST_OFFER.INTERVIEW_TIMES[interviewTimesKey].Name;
    }
    return null;
  }

  /**
   * getExamForDisplay
   * 試験内容を返す
   */
  getExamForDisplay() {
    const exams = [];
    if (this.SelectionAptitudeTestExists) {
      exams.push("適性試験");
    }
    if (this.SelectionPaperTestExists) {
      exams.push("筆記試験");
    }
    if (this.SelectionPracticalTestExists) {
      exams.push("実技試験");
    }
    if (this.SelectionOtherTestExists) {
      exams.push("その他");
    }

    const exam = exams.join(" / ");

    if (!exam) {
      return null;
    }
    return exam;
  }

  /**
   * getCasualDressFlgForDisplay
   * 表示用の面接時の服装を返す
   */
  getCasualDressFlgForDisplay() {
    return this.CasualDressFlg ? "面接時は私服OK" : "";
  }

  /**
   * getNumEventMethod
   * 有効な面接方法の個数を返す
   */
  getNumEventMethod() {
    const eventFlags = [
      this.Meeting.EnableFlg,
      this.Phone.EnableFlg,
      this.Online.EnableFlg,
    ].filter((flg) => {
      return flg === true;
    });

    return eventFlags.length;
  }

  /**
   * isMultipleEventMethod
   * 面接方法が複数あるかを返す
   */
  isMultipleEventMethod() {
    return this.getNumEventMethod() > 1;
  }

  /**
   * 面接方法が0かを返す
   */
  isNoEventMethod() {
    return this.getNumEventMethod() === 0;
  }

  /**
   * 面接情報が何もないかどうかを返す
   */
  isNoInterviewForDisplay() {
    return (
      !this.EstimatedTerm &&
      !this.getInterviewTimesForDisplay() &&
      !this.getExamForDisplay() &&
      !this.getCasualDressFlgForDisplay() &&
      !this.getInterviewerForDisplay() &&
      !this.Contact &&
      !this.Meeting.EnableFlg &&
      !this.Phone.EnableFlg &&
      !this.Online.EnableFlg &&
      (!this.WorkExperience || this.WorkExperience.isWorkExperienceNotSet())
    );
  }
}
