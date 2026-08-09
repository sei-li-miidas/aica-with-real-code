import { Record } from "immutable";

type Props = {
  /** 報酬総額（円単位） */
  Fee: number | null;
  /** 稼働時間（0.5時間単位） */
  WorkingTime: number | null;
  /** 時給（円単位） */
  HourlyFee: number | null;
  /** 補足 */
  Note: string;
};

/**
 * SpotOutsourcing
 * 業務委託（スポット）のレコード
 */
export default class SpotOutsourcing extends Record<Props>({
  Fee: null,
  WorkingTime: null,
  HourlyFee: null,
  Note: "",
}) {}
