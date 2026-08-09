import { Record } from "immutable";

type Props = {
  /** モデル年収20代 */
  Income20s: number | null;
  /** モデル年収30代 */
  Income30s: number | null;
  /** モデル年収40代 */
  Income40s: number | null;
  /** 補足 */
  Note: string;
};

/**
 * ModelAnnualIncome
 * モデル年収のレコード
 */
export default class ModelAnnualIncome extends Record<Props>({
  Income20s: null,
  Income30s: null,
  Income40s: null,
  Note: "",
}) {
  /**
   * hasSomeValue
   * ひとつでも値があるかどうか
   */
  hasSomeValue() {
    return !!(this.Income20s || this.Income30s || this.Income40s);
  }
}
