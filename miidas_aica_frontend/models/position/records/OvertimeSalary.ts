import { Record } from "immutable";

type Props = {
  /** 固定残業代の有無 */
  HasOvertimeSalary: number | null;
  /** 月額（万円単位） */
  MonthlyAmount: number | null;
  /** 見込み時間（時間単位） */
  ExpectedHours: number | null;
};

/**
 * 固定残業代のレコード
 */
export default class OvertimeSalary extends Record<Props>({
  HasOvertimeSalary: null,
  MonthlyAmount: null,
  ExpectedHours: null,
}) {}
