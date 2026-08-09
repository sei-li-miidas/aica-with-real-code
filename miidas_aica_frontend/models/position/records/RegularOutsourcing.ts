import { Record } from "immutable";

type Props = {
  /** 報酬（総額。万円単位） */
  Fee: number | null;
  /** 契約期間（1~12ヶ月） */
  ContractPeriod: number | null;
  /** 1ヶ月の稼働時間（0.5時間単位） */
  MonthlyWorkingTime: number | null;
  /** 月給（万円単位。小数点2桁まで） */
  MonthlyFee: number | null;
  /** 時給（円単位） */
  HourlyFee: number | null;
  /** インセンティブ（総額。万円単位） */
  Incentive: number;
  /** 補足 */
  Note: string;
};

/**
 * RegularOutsourcing
 * 業務委託（レギュラー）のレコード
 */
export default class RegularOutsourcing extends Record<Props>({
  Fee: null,
  ContractPeriod: null,
  MonthlyWorkingTime: null,
  MonthlyFee: null,
  HourlyFee: null,
  Incentive: 0,
  Note: "",
}) {}
