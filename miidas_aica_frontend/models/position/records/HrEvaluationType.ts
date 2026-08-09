import { Record, OrderedMap } from "immutable";

type Props = {
  /** 実力主義/年功序列 */
  Type1: number | null;
  /** 長所を伸ばす/短所を克服 */
  Type2: number | null;
  /** 成果を重視/プロセスを重視 */
  Type3: number | null;
  /** 個性重視/協調性重視 */
  Type4: number | null;
  /** 全体に対する補足 */
  Note: string;
};

/**
 * HrEvaluationType
 * 人事評価 評価基準のレコード
 */
export default class HrEvaluationType extends Record<Props>({
  Type1: null,
  Type2: null,
  Type3: null,
  Type4: null,
  Note: "",
}) {
  /**
   * getValuesOrderedMap
   * 全ての評価基準を反復順序が保障された形で取得する
   */
  getValuesOrderedMap() {
    return OrderedMap({
      Type1: this.Type1,
      Type2: this.Type2,
      Type3: this.Type3,
      Type4: this.Type4,
    });
  }
}
