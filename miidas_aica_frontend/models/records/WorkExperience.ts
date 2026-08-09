import { Record, List } from "immutable";
import MasterV2Record from "@/models/records/MasterV2";
import {
  type RecordConstructorParameter,
  type ValuesType,
} from "@/types/utility-types";

type Props = {
  /** 実施可否（ID, Nameペア） */
  Pattern: MasterV2Record;
  /** 実施タイミング（ID, Nameペア） */
  Timing: MasterV2Record;
  /** 実施日時（ID, Nameペア） */
  Timeframe: MasterV2Record;
  /** 所要時間（ID, Nameペア） */
  NeedTime: MasterV2Record;
  /** 報酬有無（ID, Nameペア） */
  Reward: MasterV2Record;
  /** 実施内容（ID, Nameペア） */
  WorkTypes: List<MasterV2Record>;
  /** 実施タイミング補足 */
  TimingRemarks: string;
  /** その他の実施タイミングの備考 */
  OtherTimingText: string;
  /** 実施内容詳細 */
  WorkContent: string;
  /** 実施日時補足 */
  TimeframeRemarks: string;
  /** 所要時間補足 */
  NeedTimeRemarks: string;
  /** 報酬金額 */
  RewardValue: number;
  /** 報酬の補足 */
  RewardRemarks: string;
};

export const WORK_EXPERIENCE_KEYS = {
  PATTERN: "Pattern",
  TIMING: "Timing",
  TIMING_REMARKS: "TimingRemarks",
  OTHER_TIMING_TEXT: "OtherTimingText",
  WORK_TYPES: "WorkTypes",
  WORK_CONTENT: "WorkContent",
  TIMEFRAME: "Timeframe",
  TIMEFRAME_REMARKS: "TimeframeRemarks",
  NEED_TIME: "NeedTime",
  NEED_TIME_REMARKS: "NeedTimeRemarks",
  REWARD: "Reward",
  REWARD_VALUE: "RewardValue",
  REWARD_REMARKS: "RewardRemarks",
} as const;

const PATTERN = {
  NOT_SET: 0, // 未設定
  OPTIONAL: 2, // 希望者のみ実施する
  DISABLED: 3, // 実施しない
};

const TIMING = {
  OTHER: 2,
};

const REWARD = {
  IS_REWARDED: 2,
};

/**
 * リアル職場体験のレコード
 */
export default class WorkExperience extends Record<Props>({
  [WORK_EXPERIENCE_KEYS.PATTERN]: new MasterV2Record({}),
  [WORK_EXPERIENCE_KEYS.TIMING]: new MasterV2Record({}),
  [WORK_EXPERIENCE_KEYS.TIMEFRAME]: new MasterV2Record({}),
  [WORK_EXPERIENCE_KEYS.NEED_TIME]: new MasterV2Record({}),
  [WORK_EXPERIENCE_KEYS.REWARD]: new MasterV2Record({}),
  [WORK_EXPERIENCE_KEYS.WORK_TYPES]: List([]),
  [WORK_EXPERIENCE_KEYS.TIMING_REMARKS]: "",
  [WORK_EXPERIENCE_KEYS.OTHER_TIMING_TEXT]: "",
  [WORK_EXPERIENCE_KEYS.WORK_CONTENT]: "",
  [WORK_EXPERIENCE_KEYS.TIMEFRAME_REMARKS]: "",
  [WORK_EXPERIENCE_KEYS.NEED_TIME_REMARKS]: "",
  [WORK_EXPERIENCE_KEYS.REWARD_VALUE]: 0,
  [WORK_EXPERIENCE_KEYS.REWARD_REMARKS]: "",
}) {
  constructor(workExperience: RecordConstructorParameter<WorkExperience>) {
    const newWorkExperience = {
      ...workExperience,
      [WORK_EXPERIENCE_KEYS.PATTERN]: new MasterV2Record(
        workExperience.Pattern ?? {},
      ),
      [WORK_EXPERIENCE_KEYS.TIMING]: new MasterV2Record(
        workExperience.Timing ?? {},
      ),
      [WORK_EXPERIENCE_KEYS.TIMEFRAME]: new MasterV2Record(
        workExperience.Timeframe ?? {},
      ),
      [WORK_EXPERIENCE_KEYS.NEED_TIME]: new MasterV2Record(
        workExperience.NeedTime ?? {},
      ),
      [WORK_EXPERIENCE_KEYS.REWARD]: new MasterV2Record(
        workExperience.Reward ?? {},
      ),
      [WORK_EXPERIENCE_KEYS.WORK_TYPES]: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        (workExperience.WorkTypes ?? []).map(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (workType) => new MasterV2Record(workType),
        ),
      ),
    };
    // @ts-expect-error: 型エラーが起きないよう後で修正する
    super(newWorkExperience);
  }

  /**
   * ラベルを返す
   */
  getLabel(key: ValuesType<typeof WORK_EXPERIENCE_KEYS>) {
    switch (key) {
      case WORK_EXPERIENCE_KEYS.PATTERN:
      case WORK_EXPERIENCE_KEYS.TIMING:
      case WORK_EXPERIENCE_KEYS.TIMEFRAME:
      case WORK_EXPERIENCE_KEYS.NEED_TIME:
      case WORK_EXPERIENCE_KEYS.REWARD:
        return this[key].Name;
      case WORK_EXPERIENCE_KEYS.WORK_TYPES:
        return this[key].map((workTypeImtRecord) => workTypeImtRecord.Name);
      case WORK_EXPERIENCE_KEYS.TIMING_REMARKS:
      case WORK_EXPERIENCE_KEYS.TIMEFRAME_REMARKS:
      case WORK_EXPERIENCE_KEYS.NEED_TIME_REMARKS:
      case WORK_EXPERIENCE_KEYS.REWARD_REMARKS:
      case WORK_EXPERIENCE_KEYS.OTHER_TIMING_TEXT:
      case WORK_EXPERIENCE_KEYS.WORK_CONTENT:
      case WORK_EXPERIENCE_KEYS.REWARD_VALUE:
        return this[key];
      default:
        return null;
    }
  }

  /**
   * リアル職場体験が未設定かどうか
   */
  isWorkExperienceNotSet() {
    return (
      !this[WORK_EXPERIENCE_KEYS.PATTERN].ID ||
      this[WORK_EXPERIENCE_KEYS.PATTERN].ID === PATTERN.NOT_SET
    );
  }

  /**
   * リアル職場体験が実施中か
   */
  isWorkExperienceEnabled() {
    const patternId = this[WORK_EXPERIENCE_KEYS.PATTERN].ID;
    return (
      patternId !== null &&
      ![PATTERN.DISABLED, PATTERN.NOT_SET].includes(patternId)
    );
  }

  /**
   * 希望者のみにリアル職場体験を実施するか
   */
  isWorkExperienceOptional() {
    return this[WORK_EXPERIENCE_KEYS.PATTERN].ID === PATTERN.OPTIONAL;
  }

  /**
   * その他の実施タイミングのテキストを表示するか
   */
  isOtherTimingTextShown() {
    return (
      this[WORK_EXPERIENCE_KEYS.TIMING].ID === TIMING.OTHER &&
      !!this.getLabel(WORK_EXPERIENCE_KEYS.OTHER_TIMING_TEXT)
    );
  }

  /**
   * 報酬額を表示するか
   */
  isRewardValueShown() {
    return this[WORK_EXPERIENCE_KEYS.REWARD].ID === REWARD.IS_REWARDED;
  }
}
