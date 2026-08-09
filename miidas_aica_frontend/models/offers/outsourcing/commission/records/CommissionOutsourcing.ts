import { Record } from "immutable";

type Props = {
  /** 業務内容 */
  BusinessDescription: string;
  /** 報酬内容 */
  Fee: string;
};

/**
 * CommissionOutsourcing
 * 業務委託（完全歩合制）求人用のレコード
 */

export default class CommissionOutsourcing extends Record<Props>({
  BusinessDescription: "",
  Fee: "",
}) {}
